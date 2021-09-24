import {loader} from 'graphql.macro';
import * as React from 'react';
import {MemoryRouter, MemoryRouterProps} from 'react-router-dom';

import {AppContext, AppContextValue} from '../app/AppContext';
import {PermissionsContext, PermissionsFromJSON} from '../app/Permissions';
import {WebSocketContext, WebSocketContextType} from '../app/WebSocketProvider';
import {PermissionFragment} from '../app/types/PermissionFragment';
import {WorkspaceProvider} from '../workspace/WorkspaceContext';

import {ApolloTestProps, ApolloTestProvider} from './ApolloTestProvider';

const typeDefs = loader('../graphql/schema.graphql');

export const PERMISSIONS_ALLOW_ALL: PermissionsFromJSON = {
  launch_pipeline_execution: true,
  launch_pipeline_reexecution: true,
  reconcile_scheduler_state: true,
  start_schedule: true,
  stop_running_schedule: true,
  start_sensor: true,
  stop_sensor: true,
  terminate_pipeline_execution: true,
  delete_pipeline_run: true,
  reload_repository_location: true,
  reload_workspace: true,
  wipe_assets: true,
  launch_partition_backfill: true,
  cancel_partition_backfill: true,
};

const testValue = {
  basePath: '',
  rootServerURI: '',
};

const websocketValue: WebSocketContextType = {
  availability: 'available',
  status: WebSocket.OPEN,
};

interface Props {
  apolloProps?: ApolloTestProps;
  appContextProps?: Partial<AppContextValue>;
  permissionOverrides?: {[permission: string]: boolean};
  routerProps?: MemoryRouterProps;
}

export const TestProvider: React.FC<Props> = (props) => {
  const {apolloProps, appContextProps, permissionOverrides, routerProps} = props;
  const permissions: PermissionFragment[] = React.useMemo(() => {
    return Object.keys(PERMISSIONS_ALLOW_ALL).map((permission) => {
      const override = permissionOverrides ? permissionOverrides[permission] : null;
      const value = typeof override === 'boolean' ? override : true;
      return {__typename: 'GraphenePermission', permission, value};
    });
  }, [permissionOverrides]);

  return (
    <AppContext.Provider value={{...testValue, ...appContextProps}}>
      <WebSocketContext.Provider value={websocketValue}>
        <PermissionsContext.Provider value={permissions}>
          <MemoryRouter {...routerProps}>
            <ApolloTestProvider {...apolloProps} typeDefs={typeDefs}>
              <WorkspaceProvider>{props.children}</WorkspaceProvider>
            </ApolloTestProvider>
          </MemoryRouter>
        </PermissionsContext.Provider>
      </WebSocketContext.Provider>
    </AppContext.Provider>
  );
};
