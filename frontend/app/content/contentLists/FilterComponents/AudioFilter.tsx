"use client";
import { useState } from "react";
import { SwitchComponent } from "./UIComponents'";
import { Button } from "@mantine/core";
import { toast } from "sonner";
import { useMutation } from "@tanstack/react-query";
import { registerJob } from "../../../api/index";
import { useRouter } from "next/navigation";

export function AudioFilter(props: any) {
  const { push } = useRouter();
  const [musicsep, setMusicsep] = useState(false);
  const [se, setSe] = useState(false);
  const [transcription, setTranscription] = useState(false);

  function sleep(ms: number) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  const createJSON = () => {
    const filters_data = {
      music_separation: {
        active: musicsep,
      },
      speech_enhancement: {
        active: se,
      },
      transcription: {
        active: transcription,
      },
    };
    const data = {
      content_id: props.id,
      content_type: "audio",
      filters: filters_data,
    };
    return data;
  };

  const { mutate, isLoading, isSuccess } = useMutation(
    (formData) => registerJob("audio", formData),
    {
      onSuccess: (data) => {
        if (data["detail"] != "Success") {
          toast.error("Failed to register job");
          return;
        } else {
          toast.success("Job registered successfully");
        }
      },
      onError: (error: any) => {
        toast.error("Failed to register job");
      },
    }
  );

  const sendJob = async () => {
    const data = createJSON();
    const jobData = {
      job_type: "audio",
      job_data: data,
    };
    mutate(jobData as any);
    props.setFilterShow(false);
    await sleep(2000);
    push("/jobs");
  };

  return (
    <div>
      <div id="music-seperation" className="">
        <div className="m-3">
          <SwitchComponent
            value={musicsep}
            setValue={setMusicsep}
            name="Stem Separation"
          />
        </div>
      </div>
      <div id="se">
        <div className="m-3">
          <SwitchComponent
            value={se}
            setValue={setSe}
            name="Speech Enhancement"
          />
        </div>
      </div>
      <div id="transcription">
        <div className="m-3">
          <SwitchComponent
            value={transcription}
            setValue={setTranscription}
            name="Transcription"
          />
        </div>
      </div>
      <div
        id="process"
        className="w-full flex justify-center items-center mb-2"
      >
        <div className="">
          <Button
            variant="outline"
            color="grape"
            radius="md"
            onClick={async () => {
              await sendJob();
            }}
          >
            Process
          </Button>
        </div>
      </div>
    </div>
  );
}
