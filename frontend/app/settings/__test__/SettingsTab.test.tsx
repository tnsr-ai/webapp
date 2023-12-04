import { render, fireEvent, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import SettingsTab from "../SettingsTab";

describe("SettingsTab", () => {
  it("toggles newsletter switch correctly", () => {
    const queryClient = new QueryClient();

    const mockProps = {
      data: {
        data: {
          newsletter: false,
          email_notification: false,
          discord_webhook: "",
        },
        verified: true,
      },
    };

    // Wrap the component with a QueryClientProvider
    render(
      <QueryClientProvider client={queryClient}>
        <SettingsTab {...mockProps} />
      </QueryClientProvider>
    );

    const newsletterSwitch = screen.getByTestId("newsletterSwitch");

    // Check initial state
    expect(newsletterSwitch).not.toBeChecked();

    // Toggle the switch
    fireEvent.click(newsletterSwitch);

    // Check if state is updated
    expect(newsletterSwitch).toBeChecked();
  });
});
