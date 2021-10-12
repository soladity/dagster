import {gql} from '@apollo/client';
import * as React from 'react';
import styled from 'styled-components/macro';

import {useFeatureFlags} from '../app/Flags';
import {SidebarSection, SidebarSubhead, SidebarTitle} from '../pipelines/SidebarComponents';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';

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
  const {flagPipelineModeTuples} = useFeatureFlags();
  const groups = groupTypes(props.types);
  console.log(groups);
  return (
    <>
      <SidebarSubhead />
      <Box padding={{vertical: 16, horizontal: 24}}>
        <SidebarTitle>{flagPipelineModeTuples ? 'Graph types' : 'Pipeline types'}</SidebarTitle>
      </Box>
      {Object.keys(groups).map((title, idx) => {
        const typesForSection = groups[title];
        const collapsedByDefault = idx !== 0 || groups[title].length === 0;

        return (
          <SidebarSection key={idx} title={title} collapsedByDefault={collapsedByDefault}>
            <Box padding={{vertical: 16, horizontal: 24}}>
              {typesForSection.length ? (
                <StyledUL>
                  {groups[title].map((type, i) => (
                    <TypeLI key={i}>
                      <TypeWithTooltip type={type} />
                    </TypeLI>
                  ))}
                </StyledUL>
              ) : (
                <div style={{color: ColorsWIP.Gray500, fontSize: '12px'}}>None</div>
              )}
            </Box>
          </SidebarSection>
        );
      })}
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

const StyledUL = styled.ul`
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
  padding: 0;
`;

const TypeLI = styled.li`
  text-overflow: ellipsis;
  overflow: hidden;
`;
