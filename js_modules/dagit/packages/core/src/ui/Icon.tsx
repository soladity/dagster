import * as React from 'react';
import styled, {createGlobalStyle} from 'styled-components/macro';

import {ColorsWIP} from './Colors';

// Based directly on Material Icons font names.
export type IconName =
  | 'account_tree'
  | 'alternate_email'
  | 'arrow_back'
  | 'arrow_downward'
  | 'arrow_drop_down'
  | 'arrow_forward'
  | 'arrow_upward'
  | 'assignment'
  | 'assignment_turned_in'
  | 'attach_file'
  | 'bolt'
  | 'cached'
  | 'cancel'
  | 'check_circle'
  | 'chevron_right'
  | 'chevron_left'
  | 'close'
  | 'delete'
  | 'done'
  | 'download_for_offline'
  | 'drag_handle'
  | 'edit'
  | 'error'
  | 'expand_less'
  | 'expand_more'
  | 'filter_alt'
  | 'folder'
  | 'folder_open'
  | 'info'
  | 'history'
  | 'layers'
  | 'linear_scale'
  | 'link'
  | 'list'
  | 'location_on'
  | 'menu'
  | 'menu_book'
  | 'open_in_new'
  | 'refresh'
  | 'schedule'
  | 'schema'
  | 'search'
  | 'sensors'
  | 'settings'
  | 'settings_backup_restore'
  | 'sort_by_alpha'
  | 'source'
  | 'speed'
  | 'splitscreen'
  | 'star'
  | 'table_view'
  | 'timer'
  | 'toggle_off'
  | 'toggle_on'
  | 'vertical_align_bottom'
  | 'vertical_align_top'
  | 'view_list'
  | 'visibility'
  | 'warning'
  | 'waterfall_chart'
  | 'workspaces'
  | 'wysiwyg'
  | 'zoom_in'
  | 'zoom_out';

interface Props {
  color?: string;
  name: IconName;
  size?: 16 | 20 | 24 | 48;
}

export const IconWIP = (props: Props) => {
  const {color = ColorsWIP.Dark, name, size = 16} = props;
  return (
    <IconWrapper $size={size} $color={color} className="material-icons">
      {name}
    </IconWrapper>
  );
};

export const IconWrapper = styled.span<{$color: string; $size: number}>`
  color: ${({$color}) => `${$color}`};
  font-size: ${({$size}) => `${$size}px`};
  user-select: none;
`;

createGlobalStyle`
  .bp3-button .material-icons {
    position: relative;
    top: 1px;
  }
  a .material-icons {
    text-decoration: none;
  }
`;
