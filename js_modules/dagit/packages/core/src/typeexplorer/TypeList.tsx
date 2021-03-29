import {gql} from '@apollo/client';
import {H3, UL} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {
  SectionInner,
  SidebarSection,
  SidebarSubhead,
  SidebarTitle,
} from '../pipelines/SidebarComponents';

import {DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT, TypeWithTooltip} from './TypeWithTooltip';
import {TypeListFragment} from './types/TypeListFragment';

interface ITypeListProps {
  types: Array<TypeListFragment>;
}

function groupTypes(types: TypeListFragment[]): {[key: string]: TypeListFragment[]} {
  const groups = {
    Custom: Array<TypeListFragment>(),
    'Built-in': Array<TypeListFragment>(),
  };
  types.forEach((type) => {
    if (type.isBuiltin) {
      groups['Built-in'].push(type);
    } else {
      groups['Custom'].push(type);
    }
  });
  return groups;
}

export const TypeList: React.FC<ITypeListProps> = (props) => {
  const groups = groupTypes(props.types);
  return (
    <>
      <SidebarSubhead />
      <SectionInner>
        <SidebarTitle>Pipeline Types</SidebarTitle>
      </SectionInner>
      {Object.keys(groups).map((title, idx) => (
        <SidebarSection key={idx} title={title} collapsedByDefault={idx !== 0}>
          <UL>
            {groups[title].map((type, i) => (
              <TypeLI key={i}>
                <TypeWithTooltip type={type} />
              </TypeLI>
            ))}
          </UL>
        </SidebarSection>
      ))}
      <H3 />
    </>
  );
};

export const TYPE_LIST_FRAGMENT = gql`
  fragment TypeListFragment on DagsterType {
    name
    isBuiltin
    ...DagsterTypeWithTooltipFragment
  }

  ${DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT}
`;

const TypeLI = styled.li`
  text-overflow: ellipsis;
  overflow: hidden;
`;
