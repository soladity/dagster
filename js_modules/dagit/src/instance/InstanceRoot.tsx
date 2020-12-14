import * as React from 'react';
import {Redirect, Route, Switch} from 'react-router-dom';

import {AssetEntryRoot} from 'src/assets/AssetEntryRoot';
import {AssetsCatalogRoot} from 'src/assets/AssetsCatalogRoot';
import {InstanceStatusRoot} from 'src/instance/InstanceStatusRoot';
import {RunRoot} from 'src/runs/RunRoot';
import {RunsRoot} from 'src/runs/RunsRoot';
import {InstanceJobsRoot} from 'src/schedules/InstanceJobsRoot';
import {SnapshotRoot} from 'src/snapshots/SnapshotRoot';
import {MainContent} from 'src/ui/MainContent';

export const InstanceRoot = () => {
  return (
    <MainContent>
      <Switch>
        <Route path="/instance/assets" exact component={AssetsCatalogRoot} />
        <Route path="/instance/assets/(/?.*)" component={AssetEntryRoot} />
        <Route path="/instance/runs" exact component={RunsRoot} />
        <Route path="/instance/runs/:runId" exact component={RunRoot} />
        <Route path="/instance/scheduler" exact component={InstanceJobsRoot} />
        <Route path="/instance/snapshots/:pipelinePath/:tab?" component={SnapshotRoot} />
        <Route
          path="/instance/:tab"
          render={({match}) => <InstanceStatusRoot tab={match.params.tab} />}
        />
        <Route path="/instance" render={() => <Redirect to="/instance/health" />} />
      </Switch>
    </MainContent>
  );
};
