import React from "react";
import styled from "styled-components/macro";
import { Colors, Icon, IconName } from "@blueprintjs/core";
import { useRouteMatch, useHistory } from "react-router-dom";
import { explorerPathFromString } from "../PipelinePathUtils";

const PIPELINE_TABS: {
  title: string;
  pathComponent: string;
  icon: IconName;
}[] = [
  { title: "Overview", pathComponent: "overview", icon: "dashboard" },
  { title: "Definition", pathComponent: "", icon: "diagram-tree" },
  {
    title: "Playground",
    pathComponent: "playground",
    icon: "manually-entered-data"
  }
];

export function tabForPipelinePathComponent(component?: string) {
  return (
    PIPELINE_TABS.find(t => t.pathComponent === component) ||
    PIPELINE_TABS.find(t => t.pathComponent === "")!
  );
}

export const PipelineNav: React.FunctionComponent = () => {
  const history = useHistory();
  const match = useRouteMatch<{ tab: string; selector: string }>([
    "/pipeline/:selector/:tab?"
  ]);
  if (!match) {
    return <span />;
  }

  const active = tabForPipelinePathComponent(match.params.tab);
  const { pipelineName } = explorerPathFromString(match.params.selector);

  return (
    <PipelineTabBarContainer>
      <PipelineName>{pipelineName}</PipelineName>
      {PIPELINE_TABS.map(tab => (
        <PipelineTab
          key={tab.title}
          tab={tab}
          active={active === tab}
          onClick={() =>
            history.push(
              `/pipeline/${match.params.selector}/${tab.pathComponent}`
            )
          }
        />
      ))}
      <div style={{ flex: 1 }} />
    </PipelineTabBarContainer>
  );
};

const PipelineTabBarContainer = styled.div`
  height: 45px;
  display: flex;
  flex-direction: row;
  align-items: center;
  border-bottom: 1px solid ${Colors.GRAY5};
  background: ${Colors.LIGHT_GRAY3};
  padding: 2px 10px;
  z-index: 3;
`;

interface PipelineTabProps {
  tab: typeof PIPELINE_TABS[0];
  active?: boolean;
  onClick: () => void;
}

class PipelineTab extends React.Component<PipelineTabProps> {
  input = React.createRef<HTMLInputElement>();

  render() {
    const { tab, onClick, active } = this.props;

    return (
      <PipelineTabContainer active={active || false} onClick={onClick}>
        <Icon icon={tab.icon} iconSize={16} style={{ paddingRight: 8 }} />
        {tab.title}
      </PipelineTabContainer>
    );
  }
}

const PipelineName = styled.div`
  font-size: 15px;
  font-weight: 500;
  padding-top: 3px;
  margin-left: 10px;
  margin-right: 30px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const PipelineTabContainer = styled.div<{ active: boolean }>`
  color: ${({ active }) => (active ? Colors.BLACK : Colors.DARK_GRAY3)};

  padding: 0 12px 3px 12px;
  display: inline-block;
  border-left: 1px solid ${Colors.GRAY4};
  user-select: none;
  cursor: ${({ active }) => (!active ? "pointer" : "inherit")};
  background: ${({ active }) => (active ? Colors.WHITE : Colors.LIGHT_GRAY1)};
  border-top: 2px solid ${({ active }) => (active ? "#2965CC" : Colors.GRAY5)};
  line-height: 33px;
  height: 40px;
  position: relative;
  white-space: nowrap;
  top: 3px;

  & .bp3-icon {
    opacity: ${({ active }) => (active ? 1 : 0.8)};
  }
  &:hover {
    background: ${({ active }) => (active ? Colors.WHITE : Colors.LIGHT_GRAY5)};
  }
  input {
    line-height: 1.28581;
    font-size: 14px;
    border: 0;
    outline: none;
  }
`;
