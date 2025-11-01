/**
 * Utility function for generating page titles in the format "Tnsrai | {page_name}"
 * 
 * @param pageName - The name of the page (e.g., "Login", "Dashboard")
 * @returns A metadata object with the formatted title
 */
export function generatePageTitle(pageName: string) {
    return {
        title: pageName,
    };
}

/**
 * Common page titles used throughout the application
 */
export const PAGE_TITLES = {
    LOGIN: "Login",
    REGISTER: "Register",
    DASHBOARD: "Dashboard",
    FORGOT_PASSWORD: "Forgot Password",
    RESET_PASSWORD: "Reset Password",
    VERIFY_EMAIL: "Verify Email",
    SETTINGS: "Settings",
    BILLING: "Billing",
    AUDIO: "Audio",
    VIDEO: "Video",
    IMAGE: "Image",
    JOBS: "Jobs",
} as const;