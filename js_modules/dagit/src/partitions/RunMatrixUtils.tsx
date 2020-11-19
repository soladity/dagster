import {Colors} from '@blueprintjs/core';
import styled from 'styled-components/macro';

export const STEP_STATUS_COLORS = {
  SUCCESS: '#009857',
  FAILURE: Colors.RED3,
  SKIPPED: Colors.GOLD3,
};

// In CSS, you can layer multiple backgrounds on top of each other by comma-separating values in
// `background`. However, this only works with gradients, not with primitive color values. To do
// hovered + red without color math (?), just stack the colors as flat gradients.
const flatGradient = (color: string) => `linear-gradient(to left, ${color} 0%, ${color} 100%)`;
const flatGradientStack = (colors: string[]) => colors.map(flatGradient).join(',');

const SuccessColorForProps = ({dimSuccesses}: {dimSuccesses?: boolean}) =>
  dimSuccesses ? '#CFE6DC' : STEP_STATUS_COLORS.SUCCESS;

export const GridColumn = styled.div<{
  disabled?: boolean;
  hovered?: boolean;
  focused?: boolean;
  multiselectFocused?: boolean;
  dimSuccesses?: boolean;
}>`
  display: flex;
  flex-direction: column;
  flex-shrink: 0;

  ${({disabled, focused, multiselectFocused, hovered}) =>
    !disabled &&
    !focused &&
    !multiselectFocused &&
    `&${hovered ? '' : ':hover'} {
    background: ${Colors.LIGHT_GRAY3};
    cursor: default;
    ${TopLabelTilted} {
      background: ${Colors.LIGHT_GRAY5};
      .tilted {
        background: ${Colors.LIGHT_GRAY3};
      }
    }
  }`}

  ${({disabled}) =>
    disabled &&
    `
      ${TopLabelTilted} {
        color: ${Colors.GRAY3}
      }
    `}

  ${({focused}) =>
    focused &&
    `background: ${Colors.BLUE4};
    ${LeftLabel} {
      color: white;
    }
    ${TopLabelTilted} {
      background: ${Colors.LIGHT_GRAY5};
      color: white;
      .tilted {
        background: ${Colors.BLUE4};
      }
    }
  }`}

  ${({multiselectFocused}) =>
    multiselectFocused &&
    `background: ${Colors.BLUE5};
    ${LeftLabel} {
      color: white;
    }
    ${TopLabelTilted} {
      background: ${Colors.LIGHT_GRAY5};
      color: white;
      .tilted {
        background: ${Colors.BLUE5};
      }
    }
  }`}

  .cell {
    height: 23px;
    display: inline-block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 12px;
    padding: 2px;
    box-sizing: border-box;
  }

  .square {
    width: 23px;
    height: 23px;
    display: inline-block;

    &:hover:not(.empty) {
      background: ${Colors.BLUE5};
    }
    &:before {
      content: ' ';
      display: inline-block;
      width: 15px;
      height: 15px;
      margin: 4px;
    }
    &.success {
      &:before {
        background: ${SuccessColorForProps};
      }
    }
    &.failure {
      &:before {
        background: ${STEP_STATUS_COLORS.FAILURE};
      }
    }
    &.failure-success {
      &:before {
        background: linear-gradient(
          135deg,
          ${STEP_STATUS_COLORS.FAILURE} 40%,
          ${SuccessColorForProps} 41%
        );
      }
    }
    &.failure-blank {
      &:before {
        background: linear-gradient(
          135deg,
          ${STEP_STATUS_COLORS.FAILURE} 40%,
          rgba(150, 150, 150, 0.3) 41%
        );
      }
    }
    &.skipped {
      &:before {
        background: ${STEP_STATUS_COLORS.SKIPPED};
      }
    }
    &.skipped-success {
      &:before {
        background: linear-gradient(
          135deg,
          ${STEP_STATUS_COLORS.SKIPPED} 40%,
          ${SuccessColorForProps} 41%
        );
      }
    }
    &.missing {
      &:before {
        background: ${Colors.WHITE};
      }
    }
    &.missing-success {
      &:before {
        background: linear-gradient(
          135deg,
          ${STEP_STATUS_COLORS.SKIPPED} 40%,
          ${SuccessColorForProps} 41%
        );
      }
    }
  }
`;

export const LeftLabel = styled.div<{hovered?: boolean; redness?: number}>`
  height: 23px;
  line-height: 23px;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  background: ${({redness, hovered}) =>
    flatGradientStack([
      redness ? `rgba(255, 0, 0, ${redness * 0.6})` : 'transparent',
      hovered ? Colors.LIGHT_GRAY2 : 'transparent',
    ])};
`;

export const TopLabel = styled.div`
  position: relative;
  height: 70px;
  padding: 4px;
  padding-bottom: 0;
  min-width: 15px;
  align-items: flex-end;
  display: flex;
`;

export const TopLabelTilted = styled.div`
  position: relative;
  height: 55px;
  padding: 4px;
  padding-bottom: 0;
  min-width: 15px;
  margin-bottom: 15px;
  align-items: end;
  display: flex;

  & > div.tilted {
    font-size: 12px;
    white-space: nowrap;
    position: absolute;
    bottom: -20px;
    left: 0;
    padding: 2px;
    padding-right: 4px;
    padding-left: 0;
    transform: rotate(-41deg);
    transform-origin: top left;
  }
`;

export const GridFloatingContainer = styled.div<{floating: boolean}>`
  display: flex;
  border-right: 1px solid ${Colors.GRAY5};
  padding-bottom: 16px;
  width: 330px;
  z-index: 2;
  ${({floating}) => (floating ? 'box-shadow: 1px 0 4px rgba(0, 0, 0, 0.15)' : '')};
`;

export const GridScrollContainer = styled.div`
  padding-right: 60px;
  padding-bottom: 16px;
  overflow-x: scroll;
  z-index: 0;
  background: ${Colors.LIGHT_GRAY5};
  flex: 1;
`;
