/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./build/employees_app/templates/**/*.html",
        "./build/clients_app/templates/**/*.html",
        "./build/employees_app/static/js/src/**/*.{js,ts,vue}",
        "./build/clients_app/static/js/src/**/*.{js,ts,vue}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    orange: '#ff6b35',
                    'orange-dark': '#e85a2b',
                    'orange-light': '#fff5f2',
                },
                sidebar: {
                    bg: '#0f172a',
                    border: 'rgba(255, 255, 255, 0.08)',
                }
            },
            fontFamily: {
                sans: ['DM Sans', 'sans-serif'],
            }
        },
    },
    plugins: [],
}
