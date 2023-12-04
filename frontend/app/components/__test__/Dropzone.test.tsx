import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react";
import DropZone from "../DropZone";
import { SingleFileUpload } from "../SingleFileUpload";
import { FileRejection } from "react-dropzone";

// Mock the SingleFileUpload component to prevent actual rendering
jest.mock("../SingleFileUpload", () => (props: any) => (
  <div data-testid="single-file-upload-mock">{props.file.name}</div>
));

const acceptedFiles = {
  "video/mp4": [".mp4"],
  "video/m4a": [".m4a"],
  "video/quicktime": [".mov"],
  "video/x-matroska": [".mkv"],
  "video/webm": [".webm"],
  "video/wmv": [".wmv"],
};

describe("DropZone", () => {
  it("should renders the dropzone component", () => {
    const { getByText } = render(
      <DropZone
        acceptedtype={acceptedFiles}
        filetype="Video files"
        setVideoUpload={jest.fn()}
        maxFileSize={10000000}
      />
    );
    expect(getByText(/click to upload/i)).toBeInTheDocument();
  });

  // Additional tests can be written to check for rejection behavior, max file size, etc.
});
