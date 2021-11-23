Azure (dagster-azure)
---------------------

Utilities for using Azure Storage Accounts with Dagster. This is mostly aimed at Azure Data Lake
Storage Gen 2 (ADLS2) but also contains some utilities for Azure Blob Storage.

|

**NOTE:** This package is incompatible with ``dagster-snowflake``! This is due to a version mismatch
between the underlying ``azure-storage-blob`` package; ``dagster-snowflake`` has a transitive
dependency on an old version, via ``snowflake-connector-python``.


.. currentmodule:: dagster_azure

.. autoconfigurable:: dagster_azure.adls2.adls2_resource
  :annotation: ResourceDefinition

.. autoclass:: dagster_azure.adls2.FakeADLS2Resource

.. autoconfigurable:: dagster_azure.adls2.adls2_file_cache
  :annotation: ResourceDefinition

.. autoclass:: dagster_azure.blob.AzureBlobComputeLogManager

.. autoconfigurable:: dagster_azure.adls2.adls2_file_manager
  :annotation: ResourceDefinition

.. autoclass:: dagster_azure.adls2.ADLS2FileHandle
  :members:

.. autoconfigurable:: dagster_azure.adls2.adls2_pickle_io_manager
  :annotation: IOManagerDefinition
