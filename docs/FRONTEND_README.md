# EnCompliance Frontend

## Purpose
The frontend application provides the user interface for the EnCompliance system. It is built with Vue.js and offers a modern, responsive design for both regular users and administrators to manage compliance requirements, documents, and reports.

## Features
- User authentication and authorization
- Compliance tracking dashboard
- Document management system
- Report generation and export
- Administrative controls
- Real-time updates and notifications

## Setup Instructions
1. Install dependencies:
   ```bash
   npm install
   ```

2. Development server:
   ```bash
   npm run dev
   ```

3. Build for production:
   ```bash
   npm run build
   ```

4. Run tests:
   ```bash
   npm run test
   ```

## Configuration
- Environment variables are managed through `.env` files
- API endpoints are configured in `src/config/api.ts`
- Theme and styling can be customized in `tailwind.config.js`

## Tailwind CSS Version and Configuration

**Important:** This project is currently pinned to **Tailwind CSS v3.4.1** due to breaking changes in Tailwind v4 that affect custom utilities and PostCSS integration.

### Why v3.4.1?
- Tailwind v4 changes how custom utilities and `@apply` work, breaking our current styling approach.
- The correct PostCSS config for v3 is:
  ```js
  export default {
    plugins: {
      tailwindcss: {},
      autoprefixer: {},
    },
  };
  ```
- Our custom utility classes (like `.font-arial`) and `@apply` usage are fully supported in v3.

### Upgrading to Tailwind v4
- If you wish to upgrade to v4 in the future, you must:
  - Refactor custom utilities to use Tailwind's plugin system or native config.
  - Remove unsupported `@apply` usage.
  - Ensure the PostCSS config uses only `tailwindcss` as a plugin.
- See the [Tailwind v4 Upgrade Guide](https://tailwindcss.com/docs/upgrade-guide) for details.

### Current Working Config
- **Tailwind version:** 3.4.1
- **PostCSS config:**
  ```js
  export default {
    plugins: {
      tailwindcss: {},
      autoprefixer: {},
    },
  };
  ```
- **tailwind.config.js:**
  - Includes custom colors, font families, and animations.
- **index.css:**
  - Uses `@apply font-arial;` in the body and defines `.font-arial` in the utilities layer.

---

**If you see unstyled pages after a dependency update, check your Tailwind and PostCSS versions/config!** 