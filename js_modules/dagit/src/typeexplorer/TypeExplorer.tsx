import * as React from "react";
import gql from "graphql-tag";
import { Link } from "react-router-dom";
import ConfigTypeSchema from "../ConfigTypeSchema";
import { TypeExplorerFragment } from "./types/TypeExplorerFragment";
import {
  SidebarSubhead,
  SidebarSection,
  SidebarTitle
} from "../SidebarComponents";

interface ITypeExplorerProps {
  type: TypeExplorerFragment;
}

export default class TypeExplorer extends React.Component<ITypeExplorerProps> {
  static fragments = {
    TypeExplorerFragment: gql`
      fragment TypeExplorerFragment on RuntimeType {
        name
        description
        inputSchemaType {
          ...ConfigTypeSchemaFragment
        }
        outputSchemaType {
          ...ConfigTypeSchemaFragment
        }
      }

      ${ConfigTypeSchema.fragments.ConfigTypeSchemaFragment}
    `
  };

  render() {
    const {
      name,
      inputSchemaType,
      outputSchemaType,
      description
    } = this.props.type;

    return (
      <div>
        <SidebarSubhead />
        <SidebarTitle>
          <Link to="?types=true">Pipeline Types</Link> > {name}
        </SidebarTitle>
        <SidebarSection title={"Description"}>
          {description || "No Description Provided"}
        </SidebarSection>
        {inputSchemaType && (
          <SidebarSection title={"Input"}>
            <ConfigTypeSchema type={inputSchemaType} />
          </SidebarSection>
        )}
        {outputSchemaType && (
          <SidebarSection title={"Output"}>
            <ConfigTypeSchema type={outputSchemaType} />
          </SidebarSection>
        )}
      </div>
    );
  }
}
