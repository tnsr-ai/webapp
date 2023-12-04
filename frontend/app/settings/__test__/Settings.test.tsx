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
jest.mock("../../components/AppBar", () => {
  const AppBarMock = () => <div>AppBar</div>;
  AppBarMock.displayName = "AppBarMock";
  return AppBarMock;
});

jest.mock("../../components/SideDrawer", () => {
  const SideDrawerMock = () => <div>SideDrawer</div>;
  SideDrawerMock.displayName = "SideDrawerMock";
  return SideDrawerMock;
});

jest.mock("../SettingsTab", () => {
  const SettingsTabMock = () => <div>SettingsTab</div>;
  SettingsTabMock.displayName = "SettingsTabMock";
  return SettingsTabMock;
});

jest.mock("../../components/ErrorTab", () => {
  const ErrorTabMock = () => <div>ErrorTab</div>;
  ErrorTabMock.displayName = "ErrorTabMock";
  return ErrorTabMock;
});

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
