import {Colors, Text} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {titleOfIO} from '../app/titleOfIO';
import {SolidColumn} from '../runs/LogsRowComponents';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {IconWIP, IconWrapper} from '../ui/Icon';
import {Code} from '../ui/Text';
import {FontFamily} from '../ui/styles';

import {SectionHeader} from './SidebarComponents';

type SolidLinkInfo = {
  solid: {name: string};
  definition: {name: string};
};

export interface SidebarSolidInvocationInfo {
  handleID: string;
  pipelineName?: string;
}

export type SolidMappingTable = {
  [key: string]: SolidLinkInfo[];
};

export const ShowAllButton = styled.button`
  background: transparent;
  border: none;
  color: ${Colors.BLUE3};
  text-decoration: underline;
  padding-top: 10px;
  font-size: 0.9rem;
`;

export const TypeWrapper = styled.div`
  margin-bottom: 10px;
`;

const SolidLink = (props: SolidLinkInfo) => (
  <Link to={`./${props.solid.name}`}>
    <Code>{titleOfIO(props)}</Code>
  </Link>
);

export const SolidLinks = (props: {title: string; items: SolidLinkInfo[]}) =>
  props.items && props.items.length ? (
    <Text>
      {props.title}
      {props.items.map((i, idx) => (
        <SolidLink key={idx} {...i} />
      ))}
    </Text>
  ) : null;

export const Invocation = (props: {
  invocation: SidebarSolidInvocationInfo;
  onClick: () => void;
}) => {
  const {handleID, pipelineName} = props.invocation;
  const handlePath = handleID.split('.');
  return (
    <InvocationContainer onClick={props.onClick}>
      {pipelineName && <div style={{color: Colors.BLUE1}}>{pipelineName}</div>}
      <SolidColumn stepKey={handlePath.join('.')} />
    </InvocationContainer>
  );
};

export const DependencyRow = ({
  from,
  to,
  isDynamic,
}: {
  from: SolidLinkInfo | string;
  to: SolidLinkInfo | string;
  isDynamic: boolean | null;
}) => {
  return (
    <tr>
      <Cell>{typeof from === 'string' ? <Code>{from}</Code> : <SolidLink {...from} />}</Cell>
      <td style={{whiteSpace: 'nowrap', textAlign: 'right'}}>
        <Group direction="row" spacing={2} alignItems="center">
          {isDynamic && <IconWIP name="bolt" color={ColorsWIP.Gray700} />}
          <IconWIP name="arrow_forward" color={ColorsWIP.Gray700} />
        </Group>
      </td>
      <Cell>{typeof to === 'string' ? <Code>{to}</Code> : <SolidLink {...to} />}</Cell>
    </tr>
  );
};

interface DependencyHeaderRowProps {
  label: string;
  style?: React.CSSProperties;
}

export const DependencyHeaderRow: React.FunctionComponent<DependencyHeaderRowProps> = ({
  label,
  ...rest
}) => (
  <tr>
    <DependencyHeaderCell {...rest}>{label}</DependencyHeaderCell>
  </tr>
);

export const ResourceHeader = styled(SectionHeader)`
  font-size: 14px;
`;

const Cell = styled.td`
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
  max-width: 0;
  width: 48%;
`;

export const ResourceContainer = styled.div`
  display: flex;
  align-items: flex-start;
  & h4 {
    margin-top: 0;
  }
  & ${IconWrapper} {
    margin-right: 8px;
  }
`;

export const DependencyTable = styled.table`
  width: 100%;
`;

const DependencyHeaderCell = styled.td`
  font-size: 0.7rem;
  color: ${Colors.GRAY3};
`;

const InvocationContainer = styled.div`
  margin: 0 -10px;
  padding: 10px;
  pointer: default;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY2};
  &:last-child {
    border-bottom: none;
  }
  &:hover {
    background: ${Colors.LIGHT_GRAY5};
  }
  font-family: ${FontFamily.monospace};
`;
