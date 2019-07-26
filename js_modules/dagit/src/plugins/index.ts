import { SidebarSolidInfoFragment } from "../types/SidebarSolidInfoFragment";

import * as ipynb from "./ipynb";
import * as sql from "./sql";
import * as generic from "./generic";

const plugins = {
  sql: sql,
  ipynb: ipynb,
  snowflake: sql
};

export interface IPluginSidebarProps {
  solid: SidebarSolidInfoFragment;
}

export interface IPluginInterface {
  SidebarComponent:
    | React.ComponentClass<IPluginSidebarProps>
    | React.SFC<IPluginSidebarProps>;
}

export function pluginForMetadata(
  metadata: { key: string; value: string }[]
): IPluginInterface | null {
  const kindMetadata = metadata.find(m => m.key === "kind");
  if (!kindMetadata) return null;
  return plugins[kindMetadata.value] || generic;
}
