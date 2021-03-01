import {Colors, Icon, Tooltip} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {DEFAULT_TIME_FORMAT, TimeFormat} from 'src/app/time/TimestampFormat';
import {TimezoneContext} from 'src/app/time/TimezoneContext';
import {timestampToString} from 'src/app/time/timestampToString';
import {Group} from 'src/ui/Group';

interface Props {
  timestamp: number;
  timezone?: string | null;
  timeFormat?: TimeFormat;
  tooltipTimeFormat?: TimeFormat;
}

export const TimestampDisplay = (props: Props) => {
  const {timestamp, timezone, timeFormat, tooltipTimeFormat} = props;
  const [userTimezone] = React.useContext(TimezoneContext);
  const locale = navigator.language;

  return (
    <Group direction="row" spacing={8} alignItems="center">
      <TabularNums>
        {timestampToString({
          timestamp: {unix: timestamp},
          locale,
          timezone: timezone || userTimezone,
          timeFormat: timeFormat,
        })}
      </TabularNums>
      {timezone && timezone !== userTimezone ? (
        <TimestampTooltip
          content={
            <TabularNums>
              {timestampToString({
                timestamp: {unix: timestamp},
                locale,
                timezone: userTimezone,
                timeFormat: tooltipTimeFormat,
              })}
            </TabularNums>
          }
        >
          <Icon icon="time" iconSize={12} color={Colors.GRAY3} style={{display: 'block'}} />
        </TimestampTooltip>
      ) : null}
    </Group>
  );
};

TimestampDisplay.defaultProps = {
  timeFormat: DEFAULT_TIME_FORMAT,
  tooltipTimeFormat: {showSeconds: false, showTimezone: true},
};

const TabularNums = styled.div`
  font-variant-numeric: tabular-nums;
`;

const TimestampTooltip = styled(Tooltip)`
  cursor: pointer;

  .bp3-popover-target {
    display: block;
  }
`;
