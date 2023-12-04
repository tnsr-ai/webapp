import { render, screen } from "@testing-library/react";
import ImageTabs from "../page";
import "@testing-library/jest-dom";

// Mock the child components used in the ImageTabs component
jest.mock("../../../components/AppBar", () => () => (
  <div data-testid="appBar">AppBar Mock</div>
));
jest.mock("../../../components/SideDrawer", () => () => (
  <div data-testid="sideDrawer">SideDrawer Mock</div>
));
jest.mock(
  "../../../content/contentLists/ContentRowList",
  () =>
    ({ content_id }: { content_id: number }) =>
      (
        <div data-testid="contentListRow">
          ContentListRow Mock - Content ID: {content_id}
        </div>
      )
);

describe("ImageTabs Component", () => {
  it("renders AppBar, SideDrawer, and ContentListRow components", () => {
    const params = { slug: "123" };
    render(<ImageTabs params={params} />);

    expect(screen.getByTestId("appBar")).toBeInTheDocument();
    expect(screen.getByTestId("sideDrawer")).toBeInTheDocument();
    expect(screen.getByTestId("contentListRow")).toBeInTheDocument();

    expect(
      screen.getByText("ContentListRow Mock - Content ID: 123")
    ).toBeInTheDocument();
  });
});
