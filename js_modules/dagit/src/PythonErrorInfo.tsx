import * as React from "react";
import styled from "styled-components/macro";
import { Button } from "@blueprintjs/core";

interface IPythonErrorInfoProps {
  showReload?: boolean;
  centered?: boolean;
  contextMsg?: string;
  error: {
    message: string;
    stack?: string[];
  };
}

export default class PythonErrorInfo extends React.Component<
  IPythonErrorInfoProps
> {
  render() {
    const { message, stack } = this.props.error;
    const Wrapper = this.props.centered ? ErrorWrapperCentered : ErrorWrapper;
    const context = this.props.contextMsg ? (
      <ErrorHeader>{this.props.contextMsg}</ErrorHeader>
    ) : null;

    return (
      <Wrapper>
        {context}
        <ErrorHeader>{message}</ErrorHeader>
        <Trace>{stack ? stack.join("") : "No Stack Provided."}</Trace>
        {this.props.showReload && (
          <Button icon="refresh" onClick={() => window.location.reload()}>
            Reload
          </Button>
        )}
      </Wrapper>
    );
  }
}

const ErrorHeader = styled.h3`
  color: #b05c47;
  font-weight: 400;
  margin: 0.5em 0 0.25em;
`;

const Trace = styled.div`
  color: rgb(41, 50, 56);
  font-family: Consolas, Menlo, monospace;
  font-size: 0.85em;
  white-space: pre;
  overflow-x: auto;
  padding-bottom: 1em;
`;

const ErrorWrapper = styled.div`
  background-color: rgba(206, 17, 38, 0.05);
  border: 1px solid #d17257;
  border-radius: 3px;
  max-width: 90vw;
  max-height: 80vh;
  padding: 1em 2em;
  overflow: auto;
`;

const ErrorWrapperCentered = styled(ErrorWrapper)`
  position: absolute;
  left: 50%;
  top: 100px;
  transform: translate(-50%, 0);
`;
