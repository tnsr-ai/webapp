import React from "react";
import { render, screen } from "@testing-library/react";
import Settings from "../page";
import { useGetSettings } from "../../api/index";
import { Loader } from "@mantine/core";
import Error from "../../components/ErrorTab";
import SettingsTab from "../SettingsTab";

// Mock the necessary modules
jest.mock("@mantine/core", () => ({
  Loader: () => <div>Loading...</div>,
}));
jest.mock("../../api/index", () => ({
  useGetSettings: jest.fn(),
}));
jest.mock("../../components/AppBar", () => () => <div>AppBar</div>);
jest.mock("../../components/SideDrawer", () => () => <div>SideDrawer</div>);
jest.mock("../SettingsTab", () => () => <div>SettingsTab</div>);
jest.mock("../../components/ErrorTab", () => () => <div>ErrorTab</div>);

describe("Settings Component", () => {
  it("should display the loader when loading", () => {
    (useGetSettings as jest.Mock).mockReturnValue({ isLoading: true });
    render(<Settings />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("should display the settings tab on success", () => {
    const mockData = { setting1: "value1" };
    (useGetSettings as jest.Mock).mockReturnValue({
      isSuccess: true,
      data: mockData,
    });
    render(<Settings />);
    expect(screen.getByText("SettingsTab")).toBeInTheDocument();
  });

  it("should display the error tab on error", () => {
    (useGetSettings as jest.Mock).mockReturnValue({ isError: true });
    render(<Settings />);
    expect(screen.getByText("ErrorTab")).toBeInTheDocument();
  });
});
