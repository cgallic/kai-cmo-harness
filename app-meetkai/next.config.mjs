/** @type {import('next').NextConfig} */
const config = {
  reactStrictMode: true,
  // Kai Marketing OS is being rolled into Gina: send app.meetkai.xyz pages there.
  // /api stays live so crons and webhooks keep working.
  async redirects() {
    return [
      {
        source: '/',
        has: [{ type: 'host', value: 'app.meetkai.xyz' }],
        destination: 'https://talktogina.ai/',
        permanent: true,
      },
      {
        source: '/:path((?!api/).*)',
        has: [{ type: 'host', value: 'app.meetkai.xyz' }],
        destination: 'https://talktogina.ai/',
        permanent: true,
      },
    ];
  },
};

export default config;
