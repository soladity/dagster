import { AppProps } from 'next/app';
import { MDXProvider, MDXProviderComponentsProp } from '@mdx-js/react';

import Layout from 'components/Layout';
import Code from 'components/Code';
import { AnchorHeadingsProvider } from 'hooks/AnchorHeadings';
import { VersionedImage } from 'components/VersionedComponents';

import 'styles/index.css';
import AnchorHeading from 'components/AnchorHeading';
import useAnchorHeadingsCleanup from 'hooks/AnchorHeadings/useAnchorHeadingsCleanup';
import useScrollToTopAfterRender from 'hooks/useScrollToTopAfterRender';
import Head from 'next/head';
import { useEffect } from 'react';

const components: MDXProviderComponentsProp = {
  h2: (props) => <AnchorHeading tag={'h2'} {...props} />,
  h3: (props) => <AnchorHeading tag={'h3'} {...props} />,
  h4: (props) => <AnchorHeading tag={'h4'} {...props} />,
  h5: (props) => <AnchorHeading tag={'h5'} {...props} />,
  h6: (props) => <AnchorHeading tag={'h6'} {...props} />,
  img: (props) => <VersionedImage {...props} />,
  pre: (props: any) => <div {...props} />,
  code: (props: any) => <Code {...props} />,
};

function App({ Component, pageProps }: AppProps) {
  useAnchorHeadingsCleanup();
  useScrollToTopAfterRender();
  // https://stackoverflow.com/a/38588927/2970704
  // This fixes the anchor position issue on Google Chrome after loading a page.
  useEffect(() => {
    if (process.browser) {
      const isChrome =
        /Chrome/.test(navigator.userAgent) &&
        /Google Inc/.test(navigator.vendor);
      if (window.location.hash && isChrome) {
        setTimeout(() => {
          const hash = window.location.hash;
          window.location.hash = '';
          window.location.hash = hash;
        }, 300);
      }
    }
  }, []);
  return (
    <>
      <Head>
        <link rel="stylesheet" href="https://rsms.me/inter/inter.css" />
      </Head>

      <MDXProvider components={components}>
        <AnchorHeadingsProvider>
          <Layout>
            <Component {...pageProps} />
          </Layout>
        </AnchorHeadingsProvider>
      </MDXProvider>
    </>
  );
}

export default App;
