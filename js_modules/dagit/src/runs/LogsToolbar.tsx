import * as React from "react";
import styled from "styled-components/macro";
import { Colors, Button, ButtonGroup } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import {
  LogLevel,
  LogFilterValue,
  GetFilterProviders,
  LogFilter
} from "./LogsProvider";
import { ComputeLogLink } from "./ComputeLogModal";
import { IStepState } from "../RunMetadataProvider";
import {
  TokenizingField,
  TokenizingFieldValue,
  SuggestionProvider
} from "../TokenizingField";
import { IRunMetadataDict } from "../RunMetadataProvider";

interface ILogsToolbarProps {
  steps: string[];
  filter: LogFilter;
  metadata: IRunMetadataDict;

  onSetFilter: (filter: LogFilter) => void;
}

const suggestionProvidersFilter = (
  suggestionProviders: SuggestionProvider[],
  values: TokenizingFieldValue[]
) => {
  // This filters down autocompletion suggestion providers based on what you've already typed.
  // It allows us to remove all autocompletions for "step:" if values already contains a step.
  const usedTokens = values.map(v => v.token).filter(Boolean);
  const singleUseTokens = ["step", "type"];

  return suggestionProviders.filter(
    ({ token }) =>
      !singleUseTokens.includes(token) || !usedTokens.includes(token)
  );
};

export default class LogsToolbar extends React.PureComponent<
  ILogsToolbarProps
> {
  render() {
    const { steps, filter, metadata, onSetFilter } = this.props;

    const selectedStep =
      filter.values.find(v => v.token === "step")?.value || null;
    const selectedStepState =
      (selectedStep && metadata.steps[selectedStep]?.state) ||
      IStepState.PREPARING;

    return (
      <LogsToolbarContainer>
        <FilterTokenizingField
          values={filter.values}
          onChangeBeforeCommit
          onChange={(values: LogFilterValue[]) =>
            onSetFilter({ ...filter, values })
          }
          suggestionProviders={GetFilterProviders(steps)}
          suggestionProvidersFilter={suggestionProvidersFilter}
          loading={false}
        />

        <LogsToolbarDivider />
        <ButtonGroup>
          {Object.keys(LogLevel).map(level => (
            <Button
              key={level}
              text={level.toLowerCase()}
              small={true}
              style={{ textTransform: "capitalize" }}
              active={filter.levels[level]}
              onClick={() =>
                onSetFilter({
                  ...filter,
                  levels: {
                    ...filter.levels,
                    [level]: !filter.levels[level]
                  }
                })
              }
            />
          ))}
        </ButtonGroup>
        {selectedStep && <LogsToolbarDivider />}
        {selectedStep && (
          <ComputeLogLink stepKey={selectedStep} runState={selectedStepState}>
            View Raw Step Output
          </ComputeLogLink>
        )}
        <div style={{ minWidth: 15, flex: 1 }} />
        <Button
          text={"Clear"}
          small={true}
          icon={IconNames.ERASER}
          onClick={() => onSetFilter({ ...filter, since: Date.now() })}
        />
        {this.props.children}
      </LogsToolbarContainer>
    );
  }
}

const LogsToolbarContainer = styled.div`
  display: flex;
  flex-direction: row;
  background: ${Colors.WHITE};
  height: 40px;
  align-items: center;
  padding: 5px 15px;
  border-bottom: 1px solid ${Colors.GRAY4};
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.07);
  z-index: 2;
`;

const LogsToolbarDivider = styled.div`
  display: inline-block;
  width: 1px;
  height: 30px;
  margin: 0 15px;
  border-right: 1px solid ${Colors.LIGHT_GRAY3};
`;

const FilterTokenizingField = styled(TokenizingField)`
  height: 20px;
  min-width: 200px;
  max-width: 800px;
  &.bp3-tag-input {
    min-height: 26px;
  }
  &.bp3-tag-input .bp3-tag-input-values {
    height: 23px;
    margin-top: 3px;
  }
`;
