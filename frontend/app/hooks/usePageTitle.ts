"use client";
import { useEffect } from "react";
import { PAGE_TITLES } from "../utils/pageTitle";

/**
 * Custom hook to dynamically set the page title for client components
 * 
 * @param pageTitle - The page title to set (can be a string from PAGE_TITLES or a custom string)
 */
export function usePageTitle(pageTitle: string) {
    useEffect(() => {
        // Set the document title with the tnsrai prefix
        document.title = `Tnsrai | ${pageTitle}`;

        // Optional: Reset to default when component unmounts
        return () => {
            document.title = "Tnsrai";
        };
    }, [pageTitle]);
}