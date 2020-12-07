import {gql, useQuery} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {InstanceDetailSummaryQuery} from 'src/nav/types/InstanceDetailSummaryQuery';

export const InstanceDetailsLink: React.FunctionComponent = () => {
  const {data} = useQuery<InstanceDetailSummaryQuery>(INSTANCE_DETAIL_SUMMARY_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  if (!data) {
    return <span />;
  }

  return (
    <div style={{color: Colors.GRAY5, fontSize: 10.5}}>
      {data.version}
      {data.instance && data.instance.info && ' | '}
      {data.instance && data.instance.info && (
        <Link to="/instance/details" style={{color: Colors.GRAY5, textDecoration: 'underline'}}>
          Instance details
        </Link>
      )}
    </div>
  );
};

export const INSTANCE_DETAIL_SUMMARY_QUERY = gql`
  query InstanceDetailSummaryQuery {
    version
    instance {
      info
    }
  }
`;
