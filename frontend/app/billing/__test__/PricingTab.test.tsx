import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { useGetRates } from "../../api/index";
import PricingTab from "../PricingTab";
import { userPlans } from "@/app/constants/constants";

jest.mock("../../api/index", () => ({
  useGetRates: jest.fn(),
}));

// Mock the sessionStorage
const sessionStorageMock = (function () {
  let store: { [key: string]: string } = {};
  return {
    getItem(key: string): string | null {
      return store[key] || null;
    },
    setItem(key: string, value: string): void {
      store[key] = value.toString();
    },
    clear(): void {
      store = {};
    },
  };
})();

Object.defineProperty(window, "sessionStorage", {
  value: sessionStorageMock,
});

describe("PricingTab Component", () => {
  const mockCountry = "US";
  const mockRates = {
    symbol: "$",
    rate: 1,
  };

  beforeEach(() => {
    // Reset sessionStorage before each test
    window.sessionStorage.clear();
    // Set up the useGetRates hook to return the mock data
    (useGetRates as jest.Mock).mockReturnValue({
      data: { data: mockRates },
      isSuccess: true,
      refetch: jest.fn(),
    });
  });

  it("renders pricing tiers correctly", () => {
    render(<PricingTab country={mockCountry} />);

    // Check that the component renders the pricing tier header
    expect(screen.getByText("Pricing Tier")).toBeInTheDocument();

    // Check that the component renders the pricing tiers
    userPlans.forEach((plan) => {
      expect(screen.getByText(plan.name)).toBeInTheDocument();
      const expectedPrice = `${mockRates.symbol} ${
        plan.times * mockRates.rate
      }`;
      expect(screen.getByText(expectedPrice)).toBeInTheDocument();
      plan.features.forEach((feature) => {
        if (feature === "No limit on duration of video") {
          expect(
            screen.getAllByText("No limit on duration of video")
          ).toHaveLength(2);
        } else {
          expect(screen.getByText(feature)).toBeInTheDocument();
        }
      });
    });
  });

  // Add more test cases as needed
});
