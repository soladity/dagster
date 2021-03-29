import {SidebarSolidDefinitionFragment} from '../pipelines/types/SidebarSolidDefinitionFragment';
import * as generic from '../plugins/generic';
import * as ipynb from '../plugins/ipynb';
import * as sql from '../plugins/sql';

const plugins = {
  sql: sql,
  ipynb: ipynb,
  snowflake: sql,
};

export interface IPluginSidebarProps {
  definition: SidebarSolidDefinitionFragment;
  rootServerURI: string;
}

interface IPluginInterface {
  SidebarComponent: React.ComponentClass<IPluginSidebarProps> | React.SFC<IPluginSidebarProps>;
}

export function pluginForMetadata(
  metadata: {key: string; value: string}[],
): IPluginInterface | null {
  const kindMetadata = metadata.find((m) => m.key === 'kind');
  if (!kindMetadata) {
    return null;
  }
  return plugins[kindMetadata.value] || generic;
}
