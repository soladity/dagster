import {gql} from '@apollo/client';
import {Button, Classes, Colors, Dialog, Icon, Position, Tooltip} from '@blueprintjs/core';
import CSS from 'csstype';
import * as React from 'react';
import ReactMarkdown from 'react-markdown';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {showCustomAlert} from 'src/CustomAlertProvider';
import {copyValue} from 'src/DomUtils';
import {assertUnreachable} from 'src/Util';
import {MetadataEntryFragment} from 'src/runs/types/MetadataEntryFragment';

export const LogRowStructuredContentTable: React.FunctionComponent<{
  rows: {label: string; item: JSX.Element}[];
  styles?: CSS.Properties;
}> = ({rows, styles}) => (
  <div style={{overflow: 'auto', paddingBottom: 10, ...(styles || {})}}>
    <StructuredContentTable cellPadding="0" cellSpacing="0">
      <tbody>
        {rows.map(({label, item}, idx) => (
          <tr key={idx} style={{display: 'flex'}}>
            <td
              style={{
                flex: 1,
                maxWidth: 'max-content',
              }}
            >
              {label}
            </td>
            <td style={{flex: 1}}>{item}</td>
          </tr>
        ))}
      </tbody>
    </StructuredContentTable>
  </div>
);

export const MetadataEntries: React.FunctionComponent<{
  entries?: MetadataEntryFragment[];
}> = ({entries}) => {
  if (!entries || !entries.length) {
    return null;
  }
  return (
    <LogRowStructuredContentTable
      rows={entries.map((entry) => ({
        label: entry.label,
        item: <MetadataEntry entry={entry} />,
      }))}
    />
  );
};

export class MetadataEntry extends React.Component<{
  entry: MetadataEntryFragment;
}> {
  static fragments = {
    MetadataEntryFragment: gql`
      fragment MetadataEntryFragment on EventMetadataEntry {
        __typename
        label
        description
        ... on EventPathMetadataEntry {
          path
        }
        ... on EventJsonMetadataEntry {
          jsonString
        }
        ... on EventUrlMetadataEntry {
          url
        }
        ... on EventTextMetadataEntry {
          text
        }
        ... on EventMarkdownMetadataEntry {
          mdStr
        }
        ... on EventPythonArtifactMetadataEntry {
          module
          name
        }
        ... on EventFloatMetadataEntry {
          floatValue
        }
        ... on EventIntMetadataEntry {
          intValue
        }
      }
    `,
  };

  render() {
    const {entry} = this.props;

    switch (entry.__typename) {
      case 'EventPathMetadataEntry':
        return (
          <>
            <MetadataEntryAction
              title={'Copy to clipboard'}
              onClick={(e) => copyValue(e, entry.path)}
            >
              {entry.path}
            </MetadataEntryAction>{' '}
            <Icon
              icon="clipboard"
              iconSize={10}
              color={'#a88860'}
              style={{verticalAlign: 'initial'}}
              onClick={(e) => copyValue(e, entry.path)}
            />
          </>
        );

      case 'EventJsonMetadataEntry':
        return (
          <MetadataEntryAction
            title="Show full value"
            onClick={() =>
              showCustomAlert({
                body: (
                  <div style={{whiteSpace: 'pre-wrap'}}>
                    {JSON.stringify(JSON.parse(entry.jsonString), null, 2)}
                  </div>
                ),
                title: 'Value',
              })
            }
          >
            [Show JSON]
          </MetadataEntryAction>
        );

      case 'EventUrlMetadataEntry':
        return (
          <>
            <MetadataEntryAction href={entry.url} title={`Open in a new tab`} target="__blank">
              {entry.url}
            </MetadataEntryAction>{' '}
            <a href={entry.url} target="__blank">
              <Icon icon="link" iconSize={10} color={'#a88860'} />
            </a>
          </>
        );
      case 'EventTextMetadataEntry':
        return entry.text;
      case 'EventMarkdownMetadataEntry':
        return <MarkdownMetadataLink title={entry.label} mdStr={entry.mdStr} />;
      case 'EventPythonArtifactMetadataEntry':
        return (
          <PythonArtifactLink
            name={entry.name}
            module={entry.module}
            description={entry.description || ''}
          />
        );
      case 'EventFloatMetadataEntry':
        return entry.floatValue;
      case 'EventIntMetadataEntry':
        return entry.intValue;
      default:
        return assertUnreachable(entry);
    }
  }
}

const PythonArtifactLink = ({
  name,
  module,
  description,
}: {
  name: string;
  module: string;
  description: string;
}) => (
  <>
    <Tooltip hoverOpenDelay={100} position={Position.TOP} content={`${module}.${name}`}>
      <span style={{cursor: 'pointer', textDecoration: 'underline'}}>{name}</span>
    </Tooltip>{' '}
    - {description}
  </>
);

class MarkdownMetadataLink extends React.Component<{
  title: string;
  mdStr: string;
}> {
  state = {isExpanded: false};
  onView = () => {
    this.setState({isExpanded: true});
  };
  onClose = () => {
    this.setState({isExpanded: false});
  };

  render() {
    const {mdStr, title} = this.props;
    const {isExpanded} = this.state;
    return (
      <>
        <MetadataEntryAction onClick={this.onView}>[Show Markdown]</MetadataEntryAction>
        {isExpanded && (
          <Dialog
            icon="info-sign"
            usePortal={true}
            style={{width: 'auto', maxWidth: '80vw'}}
            title={title}
            onClose={this.onClose}
            isOpen={true}
          >
            <MarkdownMetadataExpanded>
              <ReactMarkdown source={mdStr} />
            </MarkdownMetadataExpanded>

            <div className={Classes.DIALOG_FOOTER}>
              <div className={Classes.DIALOG_FOOTER_ACTIONS}>
                <Button intent="primary" autoFocus={true} onClick={this.onClose}>
                  Close
                </Button>
              </div>
            </div>
          </Dialog>
        )}
      </>
    );
  }
}

const MarkdownMetadataExpanded = styled.div`
  font-size: 13px;
  overflow: auto;
  max-height: 500px;
  background: ${Colors.WHITE};
  border-top: 1px solid ${Colors.LIGHT_GRAY3};
  padding: 20px;
  margin: 0;
  margin-bottom: 20px;
`;

export const MetadataEntryAction = styled.a`
  text-decoration: underline;
  color: inherit;
  &:hover {
    color: inherit;
  }
`;

export const MetadataEntryLink = styled(Link)`
  text-decoration: underline;
  color: inherit;
  &:hover {
    color: inherit;
  }
`;

const StructuredContentTable = styled.table`
  width: 100%;
  padding: 0;
  margin-top: 4px;
  border-top: 1px solid #dbc5ad;
  border-left: 1px solid #dbc5ad;
  background: #fffaf5;
  td:first-child {
    color: #a88860;
  }
  tbody > tr > td {
    padding: 4px;
    padding-right: 8px;
    border-bottom: 1px solid #dbc5ad;
    border-right: 1px solid #dbc5ad;
    vertical-align: top;
    box-shadow: none !important;
  }
`;
