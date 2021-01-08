import {Colors, Icon, Tooltip} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {TimezoneContext, timestampToString} from 'src/TimeComponents';
import {Group} from 'src/ui/Group';

interface Props {
  timestamp: number;
  timezone?: string | null;
  format: string;
  tooltipFormat: string;
}

export const TimestampDisplay = (props: Props) => {
  const {timestamp, timezone, format, tooltipFormat} = props;
  const [userTimezone] = React.useContext(TimezoneContext);

  const timestampString = timestampToString({unix: timestamp, format}, userTimezone);

  return (
    <Group direction="row" spacing={8} alignItems="center">
      <div>{timestampString}</div>
      {timezone && timezone !== userTimezone ? (
        <TimestampTooltip
          content={timestampToString({unix: timestamp, format: tooltipFormat}, timezone)}
        >
          <Icon icon="time" iconSize={12} color={Colors.GRAY3} style={{display: 'block'}} />
        </TimestampTooltip>
      ) : null}
    </Group>
  );
};

TimestampDisplay.defaultProps = {
  format: 'MMM D, YYYY, h:mm A z',
  tooltipFormat: 'MMM D, YYYY, h:mm A z',
};

const TimestampTooltip = styled(Tooltip)`
  cursor: pointer;

  .bp3-popover-target {
    display: block;
  }
`;
