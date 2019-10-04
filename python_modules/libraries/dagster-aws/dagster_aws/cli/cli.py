# -*- coding: utf-8 -*-

import os
import signal
import subprocess
import sys
import uuid

import boto3
import click
import requests
import six
import terminaltables

from dagster import seven

from .aws_util import (
    create_ec2_instance,
    create_key_pair,
    create_rds_instance,
    create_security_group,
    get_validated_ami_id,
    select_region,
    select_vpc,
)
from .config import HOST_CONFIG_FILE, EC2Config, RDSConfig
from .term import Spinner, Term, run_remote_cmd

# Client code will be deposited here on the remote EC2 instance
SERVER_CLIENT_CODE_HOME = '/opt/dagster/app/'

# DAGSTER_HOME on the remote instance
SERVER_DAGSTER_HOME = '/opt/dagster/dagster_home'

# Help text shown upon sync completion
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


def sync_dagster_yaml(ec2_config, rds_config):
    '''Configure Dagster instance to use PG storage by putting a dagster.yaml file in the remote
    DAGSTER_HOME directory
    '''
    with open(os.path.join(os.path.dirname(__file__), 'conf', 'dagster.template.yaml'), 'rb') as f:
        dagster_yaml = six.ensure_str(f.read())

    dagster_yaml = (
        dagster_yaml.replace('{username}', rds_config.username)
        .replace('{password}', rds_config.password)
        .replace('{host}', rds_config.instance_uri)
        .replace('{database}', rds_config.db_name)
    )

    tmp_file = os.path.join(seven.get_system_temp_directory(), 'dagster.yaml')

    with open(tmp_file, 'wb') as f:
        f.write(six.ensure_binary(dagster_yaml))

    rsync_to_remote(ec2_config.key_file_path, tmp_file, ec2_config.remote_host, SERVER_DAGSTER_HOME)


def ensure_requirements(base_path):
    '''Check that the user has provided a requirements.txt, and if not, create one.
    '''
    requirements_file = os.path.join(base_path, 'requirements.txt')
    if os.path.exists(requirements_file):
        Term.info('Found existing requirements.txt')
        with open(requirements_file, 'rb') as f:
            reqs = six.ensure_str(f.read()).strip().split('\n')
        if not any([req.startswith('dagster') for req in reqs]):
            Term.warning('Could not find dagster in your requirements.txt')
            click.confirm('Continue?', default=False, abort=True)
        if not any([req.startswith('dagit') for req in reqs]):
            Term.warning('Could not find dagit in your requirements.txt')
            click.confirm('Continue?', default=False, abort=True)
    else:
        Term.waiting('No requirements.txt found, creating...')
        with open(requirements_file, 'wb') as f:
            f.write(six.ensure_binary('\n'.join(['dagster', 'dagit'])))


def remove_ssh_key(key_file_path):
    # We have to clean up after ourselves to avoid "Too many authentication failures" issue.
    Term.waiting('Removing SSH key from authentication agent...')

    # AWS only gives us the private key contents; ssh-add uses the private key for adding but the
    # public key for removing
    try:
        public_keys = six.ensure_str(subprocess.check_output(['ssh-add', '-L'])).strip().split('\n')
    except subprocess.CalledProcessError:
        Term.rewind()
        Term.info('No identities found, skipping')
        return True

    filtered_public_keys = [key for key in public_keys if key_file_path in key]
    public_key = filtered_public_keys[0] if filtered_public_keys else None

    if public_key:
        tmp_pub_file = os.path.join(
            seven.get_system_temp_directory(), uuid.uuid4().hex + '-tmp-pubkey'
        )

        with open(tmp_pub_file, 'wb') as f:
            f.write(six.ensure_binary(public_key))

        res = subprocess.Popen(
            ['ssh-add', '-d', tmp_pub_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        ).communicate()
        res = six.ensure_str(res[0])

        os.unlink(tmp_pub_file)

        if 'Identity removed' in res:
            Term.rewind()
            Term.success('key deleted successfully')
            return True
        else:
            Term.warning('Could not remove key, error: %s' % res)
            return False
    else:
        Term.rewind()
        Term.info('key not found, skipping')
        return False

    return True


@click.group()
def main():
    signal.signal(signal.SIGINT, exit_gracefully)


@main.command()
@click.option('--use-master', is_flag=True, default=False)
def init(use_master):
    '''🚀 Initialize an EC2 VM to host Dagit'''
    click.echo('\n🌈 Welcome to Dagit + AWS quickstart cloud init!\n')

    # this ensures DAGSTER_HOME exists before we continue
    dagster_home = get_dagster_home()

    prev_config = None
    if EC2Config.exists(dagster_home):
        cfg_filepath = os.path.join(dagster_home, HOST_CONFIG_FILE)
        Term.warning('dagster-aws has already been initialized!\nState file:\n\t%s' % cfg_filepath)
        click.confirm('Continue?', default=False, abort=True)
        prev_config = EC2Config.load(dagster_home)

    region = select_region(prev_config)

    client = boto3.client('ec2', region_name=region)
    ec2 = boto3.resource('ec2', region_name=region)

    vpc = select_vpc(client, ec2)

    security_group_id = create_security_group(prev_config, client, ec2, vpc)

    ami_id = get_validated_ami_id(client)

    key_pair_name, key_file_path = create_key_pair(prev_config, client, dagster_home)

    inst = create_ec2_instance(client, ec2, security_group_id, ami_id, key_pair_name, use_master)

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
    '''🌱 Sync your Dagster project to the remote server.

    This command will rsync the current folder to the remote host as /opt/dagster/app, and if there
    is a requirements.txt file provided in the current folder, it will install those requirements.
    '''
    dagster_home = get_dagster_home()
    cfg = EC2Config.load(dagster_home)

    if not cfg:
        Term.fatal('No EC2 config found; run dagster-aws init first!')

    if RDSConfig.exists(dagster_home):
        rds_config = RDSConfig.load(dagster_home)
        sync_dagster_yaml(cfg, rds_config)

    if cfg.local_path is None:
        cwd = os.getcwd()
        Term.info('Local path not configured; setting to %s' % cwd)
        cfg = cfg._replace(local_path=cwd)
        cfg.save(dagster_home)

    if not os.path.exists(os.path.join(cfg.local_path, 'repository.yaml')):
        Term.fatal('No repository.yaml found in %s, create before continuing.' % cfg.local_path)

    ensure_requirements(cfg.local_path)

    rsync_to_remote(
        cfg.key_file_path,
        cfg.local_path + '/*',  # sync all files/directories in local_path
        cfg.remote_host,
        SERVER_CLIENT_CODE_HOME,
    )

    Term.waiting('Found a requirements.txt, ensuring dependencies are installed on remote host...')
    retval = run_remote_cmd(
        cfg.key_file_path,
        cfg.remote_host,
        'export PYTHONPATH=$PYTHONPATH:/opt/dagster/app && '
        'source /opt/dagster/venv/bin/activate && '
        'cd %s && pip install -r requirements.txt' % SERVER_CLIENT_CODE_HOME,
    )
    if retval == 0:
        Term.success('Install requirements.txt completed')
    else:
        Term.fatal('Error: could not install requirements.txt')

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
        'make rebuild_dagit &&'
        'sudo service dagit restart',
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

        remove_ssh_key(ec2_config.key_file_path)

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

    ec2_config = None
    if EC2Config.exists(dagster_home):
        ec2_config = EC2Config.load(dagster_home)
        click.echo(ec2_config.as_table() + '\n')
    else:
        Term.fatal('No EC2 instance configuration found; please run dagster-aws init first!')

    if RDSConfig.exists(dagster_home):
        rds_config = RDSConfig.load(dagster_home)
        click.echo(rds_config.as_table() + '\n')

    instance_uri = 'http://%s:3000' % ec2_config.remote_host

    click.echo('Instance status: ', nl=False)
    status = True
    try:
        r = requests.get(instance_uri, timeout=0.1)
        if r.status_code != 200:
            status = False
    except requests.RequestException:
        status = False

    if status:
        click.echo(click.style('[AVAILABLE]', fg='green'))
        click.echo(
            'To connect to your host, open the following URL in a browser:\n\n'
            + terminaltables.SingleTable(
                [['\n' + click.style('  %s  ' % instance_uri, fg='blue') + '\n']],
                title='Dagit Instance URI',
            ).table
        )

    else:
        click.echo(click.style('[DOWN]', fg='red'))
        Term.fatal('Could not connect to remote host %s, aborting' % instance_uri)
