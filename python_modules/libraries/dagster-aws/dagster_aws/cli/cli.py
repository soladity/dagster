# -*- coding: utf-8 -*-

import os
import signal
import subprocess
import sys

import boto3
import click

from .aws_util import (
    create_ec2_instance,
    create_key_pair,
    create_rds_instance,
    create_security_group,
    get_validated_ami_id,
    select_region,
    select_vpc,
)
from .config import EC2Config, RDSConfig
from .term import Spinner, Term, run_remote_cmd

# Client code will be deposited here on the remote EC2 instance
SERVER_CLIENT_CODE_HOME = '/opt/dagster/app/'

COMPLETED_HELP_TEXT = '''🚀 To sync your Dagster project, in your project directory, run:

    dagster-aws up

You can also open a shell on your dagster-aws instance with:

    dagster-aws shell

For full details, see dagster-aws --help'''


def get_dagster_home():
    '''Ensures that the user has set a valid DAGSTER_HOME in environment and that it exists
    '''

    dagster_home = os.getenv('DAGSTER_HOME')
    if dagster_home is None:
        Term.fatal(
            '''DAGSTER_HOME is not set! Before continuing, set with e.g.:

export DAGSTER_HOME=~/.dagster

You may want to add this line to your .bashrc or .zshrc file.
'''
        )

    Term.info('Found DAGSTER_HOME in environment at: %s' % dagster_home)

    if not os.path.isdir(dagster_home):
        Term.fatal('The specified DAGSTER_HOME folder does not exist! Create before continuing.')
    return dagster_home


def exit_gracefully(_signum, _frame):
    '''Prevent stack trace spew on Ctrl-C
    '''
    click.echo(click.style('\n\nCommand killed by keyboard interrupt, quitting\n\n', fg='yellow'))
    sys.exit(1)


def rsync_to_remote(key_file_path, local_path, remote_host, remote_path):
    remote_user = 'ubuntu'

    rsync_command = [
        'rsync',
        '-avL',
        '--progress',
        # Exclude a few common paths
        '--exclude',
        '\'.pytest_cache\'',
        '--exclude',
        '\'.git\'',
        '--exclude',
        '\'__pycache__\'',
        '--exclude',
        '\'*.pyc\'',
        '-e',
        '"ssh -i %s"' % key_file_path,
        local_path,
        '%s@%s:%s' % (remote_user, remote_host, remote_path),
    ]
    Term.info('rsyncing local path %s to %s:%s' % (local_path, remote_host, remote_path))
    click.echo('\n' + ' '.join(rsync_command) + '\n')
    subprocess.call(' '.join(rsync_command), shell=True)


@click.group()
def main():
    signal.signal(signal.SIGINT, exit_gracefully)


@main.command()
def init():
    '''🚀 Initialize an EC2 VM to host Dagit'''
    click.echo('\n🌈 Welcome to Dagit + AWS quickstart cloud init!\n')

    # this ensures DAGSTER_HOME exists before we continue
    dagster_home = get_dagster_home()

    prev_config = None
    if EC2Config.exists(dagster_home):
        click.confirm(
            'dagster-aws has already been initialized! Continue?', default=False, abort=True
        )
        prev_config = EC2Config.load(dagster_home)

    region = select_region(prev_config)

    client = boto3.client('ec2', region_name=region)
    ec2 = boto3.resource('ec2', region_name=region)

    vpc = select_vpc(client, ec2)

    security_group_id = create_security_group(prev_config, client, ec2, vpc)

    ami_id = get_validated_ami_id(client)

    key_pair_name, key_file_path = create_key_pair(prev_config, client, dagster_home)

    inst = create_ec2_instance(client, ec2, security_group_id, ami_id, key_pair_name)

    # Save host configuration for future commands
    ec2_config = EC2Config(
        remote_host=inst.public_dns_name,
        instance_id=inst.id,
        region=region,
        security_group_id=security_group_id,
        key_pair_name=key_pair_name,
        key_file_path=key_file_path,
        ami_id=ami_id,
    )
    ec2_config.save(dagster_home)

    rds_config = create_rds_instance(dagster_home, region)

    click.echo(ec2_config.as_table() + '\n')

    if rds_config:
        rds_config.save(dagster_home)
        click.echo(rds_config.as_table() + '\n')

    click.echo(click.style(COMPLETED_HELP_TEXT, fg='green'))


@main.command()
def shell():
    '''Open an SSH shell on the remote server'''
    dagster_home = get_dagster_home()
    cfg = EC2Config.load(dagster_home)

    # Lands us directly in /opt/dagster (app dir may not exist yet)
    run_remote_cmd(cfg.key_file_path, cfg.remote_host, 'cd /opt/dagster; bash')


@main.command()
@click.option(
    '-p',
    '--post-up-script',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    help='Specify a path to a script with post-init actions',
)
def up(post_up_script):
    '''🌱 Sync your Dagster project to the remote server'''
    dagster_home = get_dagster_home()
    cfg = EC2Config.load(dagster_home)

    if cfg.local_path is None:
        cwd = os.getcwd()
        Term.info('Local path not configured; setting to %s' % cwd)
        cfg = cfg._replace(local_path=cwd)
        cfg.save(dagster_home)

    if not os.path.exists(os.path.join(cfg.local_path, 'repository.yaml')):
        Term.fatal('No repository.yaml found in %s, create before continuing.' % cfg.local_path)

    rsync_to_remote(
        cfg.key_file_path,
        cfg.local_path + '/*',  # sync all files/directories in local_path
        cfg.remote_host,
        SERVER_CLIENT_CODE_HOME,
    )

    # If user has supplied a requirements.txt, install after syncing
    if os.path.exists(os.path.join(cfg.local_path, 'requirements.txt')):
        Term.waiting(
            'Found a requirements.txt, ensuring dependencies are installed on remote host...'
        )
        retval = run_remote_cmd(
            cfg.key_file_path,
            cfg.remote_host,
            'export PYTHONPATH=$PYTHONPATH:/opt/dagster/app && '
            'source /opt/dagster/venv/bin/activate && '
            'cd %s && pip install -r requirements.txt' % SERVER_CLIENT_CODE_HOME,
        )

    if post_up_script is not None:
        post_up_script = os.path.expanduser(post_up_script)

        Term.waiting('Copying user post-up script...')
        rsync_to_remote(cfg.key_file_path, post_up_script, cfg.remote_host, '/opt/dagster/')

        Term.waiting('Running user post-up script...')
        retval = run_remote_cmd(
            cfg.key_file_path,
            cfg.remote_host,
            'export PYTHONPATH=$PYTHONPATH:/opt/dagster/app && '
            'source /opt/dagster/venv/bin/activate && '
            'cd /opt/dagster/ && '
            'bash /opt/dagster/%s' % os.path.basename(post_up_script),
        )

    Term.waiting('Testing that pipeline loads correctly on remote host...')
    retval = run_remote_cmd(
        cfg.key_file_path,
        cfg.remote_host,
        'export PYTHONPATH=$PYTHONPATH:/opt/dagster/app && '
        'source /opt/dagster/venv/bin/activate && '
        'cd /opt/dagster/app/ && '
        '/opt/dagster/venv/bin/dagster pipeline list',
    )

    if retval == 0:
        Term.success('Pipeline test succeeded')
    else:
        Term.fatal('Errors in pipeline; fix before proceeding')

    Term.waiting('Restarting dagit systemd service...')
    retval = run_remote_cmd(cfg.key_file_path, cfg.remote_host, 'sudo systemctl restart dagit')
    Term.success(
        'Synchronization succeeded. To open Dagit, visit the URL:\n\thttp://%s:3000'
        % cfg.remote_host
    )


@main.command()
def update_dagster():
    '''Update the remote copy of Dagster'''
    dagster_home = get_dagster_home()
    cfg = EC2Config.load(dagster_home)

    Term.waiting(
        'Running a git pull and make rebuild_dagit on the remote dagster, this may take a while...'
    )
    retval = run_remote_cmd(
        cfg.key_file_path, cfg.remote_host, 'cd /opt/dagster/dagster && git pull'
    )
    if retval == 0:
        Term.info('Dagster git refresh completed! Rebuilding dagit...')
    else:
        Term.fatal('git pull failed')

    retval = run_remote_cmd(
        cfg.key_file_path,
        cfg.remote_host,
        'source /opt/dagster/venv/bin/activate && '
        'cd /opt/dagster/dagster/ && '
        'make rebuild_dagit',
    )
    if retval == 0:
        Term.success('Updating complete!')
    else:
        Term.fatal('Rebuilding dagit failed')


@main.command()
def delete():
    '''💥 Terminate your EC2 instance (and associated resources)'''
    dagster_home = get_dagster_home()

    already_run = EC2Config.exists(dagster_home)

    if not already_run:
        Term.fatal('No existing configuration detected, exiting')

    ec2_config = EC2Config.load(dagster_home)

    client = boto3.client('ec2', region_name=ec2_config.region)
    ec2 = boto3.resource('ec2', region_name=ec2_config.region)

    instances = ec2.instances.filter(  # pylint: disable=no-member
        InstanceIds=[ec2_config.instance_id]
    )

    Term.warning('This will terminate the following: ')
    for instance in instances:
        name = None
        for tag in instance.tags:
            if tag.get('Key') == 'Name':
                name = tag.get('Value')
        click.echo('\t%s %s %s' % (instance.id, name, instance.instance_type))

    click.confirm('\nThis step cannot be undone. Continue?', default=False, abort=True)

    Term.waiting('Terminating...')
    with Spinner():
        instances.terminate()
        waiter = client.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=[instance.id for instance in instances])

    Term.rewind()
    Term.success('Done terminating instance')

    # Wipe all instance-related configs
    ec2_config = ec2_config._replace(
        remote_host=None, instance_id=None, ami_id=None, local_path=None
    )

    # Prompt user to remove key pair
    should_delete_key_pair = click.confirm(
        'Do you also want to remove the key pair %s?' % ec2_config.key_pair_name
    )
    if should_delete_key_pair:
        client.delete_key_pair(KeyName=ec2_config.key_pair_name)
        ec2_config = ec2_config._replace(key_pair_name=None, key_file_path=None)

    # Prompt user to delete security group also
    should_remove_security_group = click.confirm(
        'Do you also want to remove the security group %s?' % ec2_config.security_group_id
    )
    if should_remove_security_group:
        client.delete_security_group(GroupId=ec2_config.security_group_id)
        ec2_config = ec2_config._replace(security_group_id=None)

    if should_delete_key_pair and should_remove_security_group:
        # Delete entirely
        ec2_config.delete(dagster_home)
    else:
        # Write out updated config
        ec2_config.save(dagster_home)

    # Prompt user to delete security group also
    if RDSConfig.exists(dagster_home):
        rds_config = RDSConfig.load(dagster_home)
        Term.warning('WARNING: A "yes" below will remove all RDS PostgreSQL data!!!')
        should_remove_rds = click.confirm(
            'Do you also want to remove the RDS instance %s?' % rds_config.instance_name
        )
        if should_remove_rds:
            rds = boto3.client('rds', region_name=ec2_config.region)
            rds.delete_db_instance(
                DBInstanceIdentifier=rds_config.instance_name,
                SkipFinalSnapshot=True,
                DeleteAutomatedBackups=True,
            )
            rds_config.delete(dagster_home)

    Term.success('Done!')


@main.command()
def info():
    '''Print out tabulated EC2/RDS configuration
    '''
    dagster_home = get_dagster_home()
    click.echo('\n')

    if EC2Config.exists(dagster_home):
        ec2_config = EC2Config.load(dagster_home)
        click.echo(ec2_config.as_table() + '\n')

    if RDSConfig.exists(dagster_home):
        rds_config = RDSConfig.load(dagster_home)
        click.echo(rds_config.as_table() + '\n')
