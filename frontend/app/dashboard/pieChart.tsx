import * as React from "react";
import { PieChart } from "@mui/x-charts/PieChart";

const data = [
  { id: 0, value: 10, label: "series A" },
  { id: 1, value: 15, label: "series B" },
  { id: 2, value: 20, label: "series C" },
];

interface DataProps {
  storageData: {
    video: number;
    audio: number;
    image: number;
  };
}

export default function PieActiveArc({ storageData }: DataProps) {
  const data = [
    {
      id: 0,
      value: storageData.video,
      label: "Video",
    },
    { id: 1, value: storageData.audio, label: "Audio" },
    { id: 2, value: storageData.image, label: "Image" },
  ];
  return (
    <PieChart
      series={[
        {
          data,
          highlightScope: { faded: "global", highlighted: "item" },
          faded: { innerRadius: 30, additionalRadius: -30, color: "gray" },
        },
      ]}
      height={200}
    />
  );
}
