import {Button, Menu} from '@blueprintjs/core';
import {Select} from '@blueprintjs/select';
import moment from 'moment-timezone';
import React from 'react';

export const browserTimezone = () => Intl.DateTimeFormat().resolvedOptions().timeZone;
const browserTimezoneAbbreviation = () => moment.tz(browserTimezone()).format('z');

type TimestampProps = ({ms: number} | {unix: number}) & {
  format?: string;
};

const defaultTimeFormat = (m: moment.Moment, timezone: string) => {
  if (timezone === 'UTC') {
    return 'YYYY-MM-DD HH:mm';
  }

  const now = moment(Date.now());
  if (timezone !== 'Automatic') {
    now.tz(timezone);
  }

  return m.year() === now.year() ? 'MMM D, h:mm A' : 'MMM D, YYYY, h:mm A';
};

// This helper is here so that we can swap out Moment in the future as needed and
// encourage use of the same default format string across the app.
export function timestampToString(time: TimestampProps, timezone: string) {
  let m = 'ms' in time ? moment(time.ms) : moment.unix(time.unix);
  if (timezone !== 'Automatic') {
    m = m.tz(timezone);
  }

  return m.format(time.format || defaultTimeFormat(m, timezone));
}

export const Timestamp: React.FunctionComponent<TimestampProps> = (props) => {
  const [timezone] = React.useContext(TimezoneContext);
  return <>{timestampToString(props, timezone)}</>;
};

const TimezoneStorageKey = 'TimezonePreference';

export const TimezoneContext = React.createContext<[string, (next: string) => void]>([
  'UTC',
  () => {},
]);

export const TimezoneProvider: React.FunctionComponent = (props) => {
  const [value, setValue] = React.useState(
    window.localStorage.getItem(TimezoneStorageKey) || 'Automatic',
  );
  const onChange = (tz: string) => {
    window.localStorage.setItem(TimezoneStorageKey, tz);
    setValue(tz);
  };
  return (
    <TimezoneContext.Provider value={[value, onChange]}>{props.children}</TimezoneContext.Provider>
  );
};

const formatOffset = (mm: number) => {
  const amm = Math.abs(mm);
  // moment.tz.zone() offsets are inverted: https://momentjs.com/timezone/docs/#/zone-object/offset/
  return `${mm < 0 ? '+' : '-'}${Math.floor(amm / 60)}:${amm % 60 < 10 ? '0' : ''}${amm % 60}`;
};

const AllTimezoneItems = moment.tz
  .names()
  .map((key) => {
    const offset = moment.tz.zone(key)?.utcOffset(Date.now()) || 0;
    return {offsetLabel: `${formatOffset(offset)}`, offset, key};
  })
  .sort((a, b) => a.offset - b.offset);

const PopularTimezones = ['UTC', 'US/Pacific', 'US/Mountain', 'US/Central', 'US/Eastern'];

const automaticLabel = () => `Automatic (${browserTimezoneAbbreviation()})`;

const SortedTimezoneItems = [
  {
    key: automaticLabel(),
    offsetLabel: '',
    offset: 0,
  },
  {
    key: 'divider-1',
    offsetLabel: '',
    offset: 0,
  },
  ...AllTimezoneItems.filter((t) => PopularTimezones.includes(t.key)),
  {
    key: 'divider-2',
    offsetLabel: '',
    offset: 0,
  },
  ...AllTimezoneItems.filter((t) => !PopularTimezones.includes(t.key)),
];

export const TimezonePicker: React.FunctionComponent = () => {
  const [timezone, setTimezone] = React.useContext(TimezoneContext);

  return (
    <div className="bp3-dark" style={{padding: 5, flexShrink: 0}}>
      <Select<typeof SortedTimezoneItems[0]>
        activeItem={SortedTimezoneItems.find((tz) => tz.key === timezone)}
        items={SortedTimezoneItems}
        itemPredicate={(query, tz) => tz.key.toLowerCase().includes(query.toLowerCase())}
        itemRenderer={(tz, props) =>
          tz.key.startsWith('divider') ? (
            <Menu.Divider key={tz.key} />
          ) : (
            <Menu.Item
              active={props.modifiers.active}
              onClick={props.handleClick}
              label={tz.offsetLabel}
              key={tz.key}
              text={tz.key}
            />
          )
        }
        noResults={<Menu.Item disabled={true} text="No results." />}
        onItemSelect={(tz) => setTimezone(tz.key)}
      >
        <Button small text={timezone === 'Automatic' ? automaticLabel() : timezone} icon="time" />
      </Select>
    </div>
  );
};
