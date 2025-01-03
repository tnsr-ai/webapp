"use client";
import { useEffect, useState } from "react";
import { SwitchComponent } from "./UIComponents'";
import { Button } from "@mantine/core";
import { toast } from "sonner";
import { useMutation } from "@tanstack/react-query";
import { registerJob, getJobEstimate } from "../../../api/index";
import { useRouter } from "next/navigation";

interface AudioModel {
  id: number;
  name: string;
}

interface FiltersData {
  [key: string]: {
    active: boolean;
    model?: string;
    factor?: AudioModel;
  };
}

interface CreateJsonData {
  content_id: string;
  content_type: string;
  filters: FiltersData;
}

function capitalizeFirstChar(word: string) {
  if (!word) return "";
  return word.charAt(0).toUpperCase() + word.slice(1);
}
export function AudioFilter(props: any) {
  const userTier = props.filterConfig["user_tier"];
  const tierConfig = props.filterConfig["model_tier"][userTier];
  const maxFilter = tierConfig["audio"]["max_filters"] as number;
  const [userMsg, setUserMsg] = useState("");
  const [estimate, setEstimate] = useState("");
  const [eta, setETA] = useState("");
  const [enabledFilters, setEnabledFilters] = useState<string[]>([]);
  const [disabledFilters, setDisabledFilters] = useState<string[]>([]);
  const router = useRouter();
  const [musicsep, setMusicsep] = useState(false);
  const [se, setSe] = useState(false);
  const [transcription, setTranscription] = useState(false);
  const [showProcess, setShowProcess] = useState(false);

  function sleep(ms: number) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function filterDisableCheck(filterName: string) {
    if (enabledFilters.length < maxFilter) {
      return false;
    }
    return !enabledFilters.includes(filterName);
  }

  const createJSON = (): CreateJsonData => {
    const filters_data = {
      stem_seperation: {
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
      onSuccess: async (data) => {
        if (data["detail"] != "Success") {
          toast.error(data["detail"]);
          return;
        } else {
          toast.success("Job registered successfully");
          await sleep(2000);
          router.push("/jobs");
        }
      },
      onError: (error: any) => {
        toast.error("Failed to register job");
      },
    }
  );

  const getEstimate = useMutation(
    (jobData) => getJobEstimate(props.content_data["id"], jobData),
    {
      onSuccess: async (data) => {
        setEstimate(`${data["price"]}`);
        setETA(`${data["eta"]}`);
      },
      onError: () => {
        setEstimate(`Error`);
        setShowProcess(false);
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
  };

  useEffect(() => {
    let jobCount = 0;
    const filtersData = createJSON()["filters"];
    for (const [key, value] of Object.entries(filtersData)) {
      if (filtersData[key]["active"] === true) {
        getEstimate.mutate(filtersData as any);
      }
    }
    const newEnabledFilters = [];
    const newDisabledFilters = [];

    for (let key in filtersData) {
      if (filtersData[key]["active"] === true) {
        jobCount += 1;
        newEnabledFilters.push(key);
      } else {
        newDisabledFilters.push(key);
      }
    }

    if (jobCount === 0) {
      setShowProcess(false);
    } else if (jobCount < maxFilter) {
      setUserMsg("");
      setShowProcess(true);
    } else if (jobCount === maxFilter) {
      setUserMsg(
        `Max ${maxFilter} filters allowed for ${capitalizeFirstChar(
          userTier
        )} tier`
      );
      setShowProcess(true);
    } else {
      setUserMsg("");
      setShowProcess(false);
    }

    setEnabledFilters(newEnabledFilters);
    setDisabledFilters(newDisabledFilters);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [musicsep, se, transcription, maxFilter]);

  return (
    <div className="overflow-y-auto">
      <div id="speech_enhancement">
        <div className="m-3">
          <SwitchComponent
            value={se}
            setValue={setSe}
            name="Speech Enhancement"
            disabled={filterDisableCheck("speech_enhancement")}
          />
        </div>
      </div>
      <div id="transcription">
        <div className="m-3">
          <SwitchComponent
            value={transcription}
            setValue={setTranscription}
            name="Transcription"
            disabled={filterDisableCheck("transcription")}
          />
          {transcription === true && (
            <p className="font-semibold pl-[52px]">Generate .srt file*</p>
          )}
        </div>
        <div id="stem_seperation" className="w-full">
          <div className="ml-3 mr-3 mt-3 mb-2 flex-row">
            <SwitchComponent
              value={musicsep}
              setValue={setMusicsep}
              name="Audio Separation"
              disabled={filterDisableCheck("stem_seperation")}
            />
            {musicsep === true && (
              <p className="font-semibold pl-[52px]">Output will be zipped*</p>
            )}
          </div>
        </div>
      </div>
      {showProcess === true && (
        <div className="ml-3">
          <p>
            Credit:{" "}
            <span className="font-bold text-purple-500">{estimate}</span>
          </p>
        </div>
      )}
      {showProcess === true && (
        <div className="ml-3 mt-1">
          <p>
            ETA:{" "}
            <span className="font-bold text-purple-500 text-base">~{eta}</span>
          </p>
        </div>
      )}
      {showProcess === true && (
        <div>
          <div className="ml-3 mb-2">
            <p>{userMsg}</p>
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
      )}
      {showProcess === false && (
        <div className="ml-3 mb-4">
          <p>{userMsg}</p>
        </div>
      )}
    </div>
  );
}
