import * as React from "react";
import gql from "graphql-tag";
import { LogsFilterProviderMessageFragment } from "./types/LogsFilterProviderMessageFragment";
import { isEqual } from "lodash";

export enum LogLevel {
  DEBUG = "DEBUG",
  INFO = "INFO",
  WARNING = "WARNING",
  ERROR = "ERROR",
  CRITICAL = "CRITICAL"
}

export const DefaultLogFilter = {
  levels: Object.assign(
    Object.keys(LogLevel).reduce((dict, key) => ({ ...dict, [key]: true }), {}),
    { [LogLevel.DEBUG]: false }
  ),
  text: "",
  since: 0
};

export interface ILogFilter {
  text: string;
  levels: { [key: string]: boolean };
  since: number;
}

interface ILogsFilterProviderProps<T> {
  filter: ILogFilter;
  nodes: T[] | undefined;
  children: (props: {
    filteredNodes: T[] | undefined;
    busy: boolean;
  }) => React.ReactChild;
}

interface ILogsFilterProviderState<T> {
  results: T[] | undefined;
}

export default class LogsFilterProvider<
  T extends LogsFilterProviderMessageFragment
> extends React.Component<
  ILogsFilterProviderProps<T>,
  ILogsFilterProviderState<T>
> {
  static fragments = {
    LogsFilterProviderMessageFragment: gql`
      fragment LogsFilterProviderMessageFragment on PipelineRunEvent {
        ... on MessageEvent {
          message
          timestamp
          level
          step {
            key
          }
        }
      }
    `
  };

  state: ILogsFilterProviderState<T> = {
    results: []
  };

  componentDidMount() {
    this.runFilter();
  }

  componentDidUpdate(prevProps: ILogsFilterProviderProps<T>) {
    if (
      prevProps.filter !== this.props.filter ||
      prevProps.nodes !== this.props.nodes
    ) {
      this.runFilter();
    }
  }

  runFilter = () => {
    const { nodes, filter } = this.props;

    if (nodes === undefined) {
      this.setState({ results: nodes });
      return;
    }

    const textLower = filter.text.toLowerCase();
    const nextResults = nodes.filter(node => {
      if (!filter.levels[node.level]) return false;
      if (filter.since && Number(node.timestamp) < filter.since) return false;

      if (filter.text) {
        if (filter.text.startsWith("step:")) {
          return node.step && node.step.key === filter.text.substr(5);
        } else {
          return node.message.toLowerCase().includes(textLower);
        }
      }
      return true;
    });

    this.setState({ results: nextResults });
  };

  render() {
    return this.props.children({
      filteredNodes: this.state.results,
      busy: false
    });
  }
}
