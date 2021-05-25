import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';
import {hyphenatedName} from '../testing/defaultMocks';

import {AssetDetails} from './AssetDetails';

describe('AssetDetails', () => {
  const defaultMocks = {
    EventMetadataEntry: () => ({
      __typename: 'EventAssetMetadataEntry',
      label: hyphenatedName,
      jsonString: () => '[]',
    }),
  };

  describe('Historical materialization alert', () => {
    it('does not show alert if no `asOf` is provided', async () => {
      render(
        <TestProvider apolloProps={{mocks: defaultMocks}}>
          <AssetDetails assetKey={{path: ['foo']}} asOf={null} />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(screen.queryByText(/this is a historical asset snapshot\./i)).toBeNull();
      });
    });

    it('does not show alert if timestamps match', async () => {
      const mocks = {
        ...defaultMocks,
        Asset: () => ({
          assetMaterializations: () => new MockList(1),
        }),
        StepMaterializationEvent: () => ({
          timestamp: () => '123',
        }),
      };
      render(
        <TestProvider apolloProps={{mocks}}>
          <AssetDetails assetKey={{path: ['foo']}} asOf="123" />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(screen.queryByText(/this is a historical asset snapshot\./i)).toBeNull();
      });
    });

    it('does show alert if timestamps do not match', async () => {
      let counter = 100;
      const mocks = {
        ...defaultMocks,
        StepMaterializationEvent: () => ({
          timestamp: () => `${counter--}`,
        }),
      };

      render(
        <TestProvider apolloProps={{mocks}}>
          <AssetDetails assetKey={{path: ['foo']}} asOf="99" />
        </TestProvider>,
      );

      await waitFor(() => {
        expect(screen.queryByText(/this is a historical asset snapshot\./i)).toBeVisible();
      });
    });
  });
});
