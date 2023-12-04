"use client";
import { useState, useCallback } from "react";
import { FileError, FileRejection, useDropzone, Accept } from "react-dropzone";
import React from "react";
import { SingleFileUpload } from "./SingleFileUpload";

export interface UploadableFile {
  file: File;
  errors: FileError[];
}

interface DropZoneProps {
  acceptedtype: Accept;
  filetype: string;
  setVideoUpload: any;
  maxFileSize: number;
}

export default function DropZone(props: DropZoneProps) {
  const [files, setFiles] = useState<UploadableFile[]>([]);
  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFile: FileRejection[]) => {
      const mappedAcc = acceptedFiles.map((file) => ({ file, errors: [] }));
      setFiles((curr) => [...curr, ...mappedAcc, ...rejectedFile]);
    },
    []
  );
  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: props.acceptedtype,
    maxFiles: 1,
    multiple: false,
  });

  return (
    <div>
      <div
        className="flex items-center justify-center max-w-[1200px] m-auto mt-5 px-5"
        {...getRootProps()}
      >
        <label
          htmlFor="dropzone-file"
          data-testid="dropzone-file"
          className="flex flex-col items-center justify-center w-full h-48 border-2 border-gray-300 border-dashed rounded-xl cursor-pointer bg-gray-50 dark:hover:bg-bray-800 dark:bg-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:hover:border-gray-500 dark:hover:bg-gray-600"
        >
          <div className="flex flex-col items-center justify-center pt-5 pb-6">
            <svg
              aria-hidden="true"
              className="w-10 h-10 mb-3 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              ></path>
            </svg>
            <p className="mb-2 text-sm text-gray-500 dark:text-gray-400 px-3 text-center">
              <span className="font-semibold">Click to upload</span> or drag and
              drop
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 px-3 text-center">
              {props.filetype}
            </p>
          </div>
          <input {...getInputProps()} />
        </label>
      </div>
      {files.map((fileWrapper, index) => (
        <div key={index}>
          <SingleFileUpload
            file={fileWrapper.file}
            filetype={props.acceptedtype}
            setVideoUpload={props.setVideoUpload}
            maxFileSize={props.maxFileSize}
          />
        </div>
      ))}
    </div>
  );
}
