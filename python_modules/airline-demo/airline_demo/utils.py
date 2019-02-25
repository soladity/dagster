import errno
import os

import boto3
import sqlalchemy

from botocore.handlers import disable_signing


def mkdir_p(newdir, mode=0o777):
    """The missing mkdir -p functionality in os."""
    try:
        os.makedirs(newdir, mode)
    except OSError as err:
        # Reraise the error unless it's about an already existing directory
        if err.errno != errno.EEXIST or not os.path.isdir(newdir):
            raise


def create_s3_session(signed=True):
    s3 = boto3.resource('s3').meta.client  # pylint:disable=C0103
    if not signed:
        s3.meta.events.register('choose-signer.s3.*', disable_signing)
    return s3


def create_redshift_db_url(username, password, hostname, db_name, jdbc=True):
    if jdbc:
        db_url = (
            'jdbc:postgresql://{hostname}:5432/{db_name}?'
            'user={username}&password={password}'.format(
                username=username, password=password, hostname=hostname, db_name=db_name
            )
        )
    else:
        db_url = "redshift_psycopg2://{username}:{password}@{hostname}:5439/{db_name}".format(
            username=username, password=password, hostname=hostname, db_name=db_name
        )
    return db_url


def create_redshift_engine(db_url):
    return sqlalchemy.create_engine(db_url)


def create_postgres_db_url(username, password, hostname, db_name, jdbc=True):
    if jdbc:
        db_url = (
            'jdbc:postgresql://{hostname}:5432/{db_name}?'
            'user={username}&password={password}'.format(
                username=username, password=password, hostname=hostname, db_name=db_name
            )
        )
    else:
        db_url = 'postgresql://{username}:{password}@{hostname}:5432/{db_name}'.format(
            username=username, password=password, hostname=hostname, db_name=db_name
        )
    return db_url


def create_postgres_engine(db_url):
    return sqlalchemy.create_engine(db_url)


class S3Logger(object):
    def __init__(self, logger, bucket, key, filename, size):
        self._logger = logger
        self._bucket = bucket
        self._key = key
        self._filename = filename
        self._seen_so_far = 0
        self._size = size

    def __call__(self, bytes_amount):
        self._seen_so_far += bytes_amount
        percentage = (self._seen_so_far / self._size) * 100
        self._logger(
            'Download of {bucket}/{key} to {target_path}: {percentage}% complete'.format(
                bucket=self._bucket,
                key=self._key,
                target_path=self._filename,
                percentage=percentage,
            )
        )
