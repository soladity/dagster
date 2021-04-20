import {execSync} from 'child_process';
import {writeFileSync} from 'fs';

import {buildClientSchema, getIntrospectionQuery, printSchema} from 'graphql';

const pyVer = execSync('python --version').toString();
const verMatch = pyVer.match(/Python ([\d.]*)/);
if (!(verMatch != null && verMatch.length >= 2 && parseFloat(verMatch[1]) >= 3.6)) {
  const errMsg =
    pyVer !== '' ? pyVer : 'nothing on stdout indicating no python or a version earlier than 3.4';
  throw new Error(`Must use Python version >= 3.6 got ${errMsg}`);
}

// https://github.com/dagster-io/dagster/issues/2623
const result = execSync(
  `dagster-graphql --ephemeral-instance --empty-workspace -t '${getIntrospectionQuery({
    descriptions: false,
  })}'`,
  {cwd: '../../../../examples/docs_snippets/'},
).toString();

const schemaJson = JSON.parse(result).data;

// Write schema.graphql in the SDL format
const sdl = printSchema(buildClientSchema(schemaJson));
writeFileSync('./src/graphql/schema.graphql', sdl);

// Write `possibleTypes.generated.json`, used for creating a mocked schema in tests.
const possibleTypes = {};

schemaJson.__schema.types.forEach((supertype: {name: string; possibleTypes: [{name: string}]}) => {
  if (supertype.possibleTypes) {
    possibleTypes[supertype.name] = supertype.possibleTypes.map((subtype) => subtype.name);
  }
});

writeFileSync('./src/graphql/possibleTypes.generated.json', JSON.stringify(possibleTypes));
