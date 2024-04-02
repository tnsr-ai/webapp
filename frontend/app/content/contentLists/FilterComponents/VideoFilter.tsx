"use client";
import { Button } from "@mantine/core";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { registerJob } from "../../../api/index";
import { CustomDropdown, SwitchComponent } from "./UIComponents'";

interface VideoModel {
  id: number;
  name: string;
}

interface FiltersData {
  [key: string]: {
    active: boolean;
    model?: string;
    factor?: VideoModel;
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

export function VideoFilter(props: any) {
  const userTier = props.filterConfig["user_tier"];
  const tierConfig = props.filterConfig["model_tier"][userTier];
  const maxFilter = tierConfig["video"]["max_filters"] as number;
  const [userMsg, setUserMsg] = useState("");
  const [enabledFilters, setEnabledFilters] = useState<string[]>([]);
  const [disabledFilters, setDisabledFilters] = useState<string[]>([]);
  const router = useRouter();

  const video_models = [
    { id: 1, name: "SuperRes 2x v1 (Faster)" },
    { id: 2, name: "SuperRes 4x v1 (Faster)" },
    { id: 3, name: "SuperRes 2x v2 (Slower, better result)" },
    { id: 4, name: "SuperRes 4x v2 (Slower, better result)" },
    { id: 5, name: "SuperRes Anime (For Animated content)" },
  ];

  const slowmo_factor = [
    { id: 1, name: "2x" },
    { id: 2, name: "4x" },
  ];

  const [SRActive, setSRActive] = useState(false);
  const [deblur, setDeblur] = useState(false);
  const [denoise, setDenoise] = useState(false);
  const [facerestore, setFacerestore] = useState(false);
  const [colorizer, setColorizer] = useState(false);
  const [slowmo, setSlowmo] = useState(false);
  const [interpolation, setInterpolation] = useState(false);
  const [deinterlace, setDeinterlace] = useState(false);
  const [speech, setSpeech] = useState(false);
  const [transcription, setTranscription] = useState(false);
  const [voiceDisabled, setVoiceDisabled] = useState(false);
  const [slowmodisabled, setSlowmodisabled] = useState(false);
  const [showProcess, setShowProcess] = useState(false);
  const [modelType, setModelType] = useState<VideoModel>(video_models[0]);
  const [slowmofactor, setSlowmoFactor] = useState<VideoModel>(
    slowmo_factor[0]
  );

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
    const filters_data: FiltersData = {
      super_resolution: {
        active: SRActive,
        model: modelType.name,
      },
      video_deblurring: {
        active: deblur,
      },
      video_denoising: {
        active: denoise,
      },
      face_restoration: {
        active: facerestore,
      },
      bw_to_color: {
        active: colorizer,
      },
      slow_motion: {
        active: slowmo,
        factor: slowmofactor,
      },
      video_interpolation: {
        active: interpolation,
      },
      video_deinterlacing: {
        active: deinterlace,
      },
      speech_enhancement: {
        active: speech,
      },
      transcription: {
        active: transcription,
      },
    };
    const data: CreateJsonData = {
      content_id: props.id,
      content_type: "video",
      filters: filters_data,
    };
    return data;
  };

  const { mutate, isLoading, isSuccess } = useMutation(
    (formData) => registerJob("video", formData),
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
      onError: () => {
        toast.error("Failed to register job");
      },
    }
  );

  const sendJob = async () => {
    const data = createJSON();
    const jobData = {
      job_type: "video",
      job_data: data,
    };
    mutate(jobData as any);
    props.setFilterShow(false);
  };

  useEffect(() => {
    if (slowmo) {
      if (speech) {
        setSpeech(false);
        setEnabledFilters(
          enabledFilters.filter((f) => f !== "speech_enhancement")
        );
      }
      if (transcription) {
        setTranscription(false);
        setEnabledFilters(enabledFilters.filter((f) => f !== "transcription"));
      }
      setVoiceDisabled(true);
    } else {
      setVoiceDisabled(false);
    }

    // Handle the disabling of slow motion when speech or transcription is active
    if (speech || transcription) {
      if (slowmo) {
        setSlowmo(false);
      }
      setEnabledFilters(enabledFilters.filter((f) => f !== "slow_motion"));
      setSlowmodisabled(true);
    } else {
      setSlowmodisabled(false);
    }
    let jobCount = 0;
    const filtersData = createJSON()["filters"];
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
  }, [
    slowmo,
    speech,
    transcription,
    SRActive,
    deblur,
    denoise,
    facerestore,
    colorizer,
    interpolation,
    deinterlace,
    maxFilter,
  ]);

  return (
    <div className="overflow-y-auto">
      <div id="super_resolution" className="">
        <div className="m-3">
          <SwitchComponent
            value={SRActive}
            setValue={setSRActive}
            name="Super Resolution"
            disabled={filterDisableCheck("super_resolution")}
          />
          <div>
            {SRActive ? (
              <CustomDropdown
                value={video_models}
                name="Model"
                type={modelType}
                setType={setModelType}
              />
            ) : null}
          </div>
        </div>
      </div>
      <div id="video_deblurring">
        <div className="m-3">
          <SwitchComponent
            value={deblur}
            setValue={setDeblur}
            name="Video Deblurring"
            disabled={filterDisableCheck("video_deblurring")}
          />
        </div>
      </div>
      <div id="video_denoising">
        <div className="m-3">
          <SwitchComponent
            value={denoise}
            setValue={setDenoise}
            name="Video Denoising"
            disabled={filterDisableCheck("video_denoising")}
          />
        </div>
      </div>
      <div id="face_restoration">
        <div className="m-3">
          <SwitchComponent
            value={facerestore}
            setValue={setFacerestore}
            name="Face Restoration"
            disabled={filterDisableCheck("face_restoration")}
          />
        </div>
      </div>
      <div id="bw_to_color">
        <div className="m-3">
          <SwitchComponent
            value={colorizer}
            setValue={setColorizer}
            name="B/W to Color"
            disabled={filterDisableCheck("bw_to_color")}
          />
        </div>
      </div>
      <div id="slow_motion" className="">
        <div className="m-3">
          <SwitchComponent
            value={slowmo}
            setValue={setSlowmo}
            name="Slow Motion"
            disabled={slowmodisabled || filterDisableCheck("slow_motion")}
          />
          <div>
            {slowmo ? (
              <CustomDropdown
                value={slowmo_factor}
                name=<p>
                  Slow Motion Factor{" "}
                  <span className="font-semibold text-red-500">
                    (Removes audio)*
                  </span>
                </p>
                type={slowmofactor}
                setType={setSlowmoFactor}
              />
            ) : null}
          </div>
        </div>
      </div>
      <div id="video_interpolation">
        <div className="m-3">
          <SwitchComponent
            value={interpolation}
            setValue={setInterpolation}
            name="Video Interpolation"
            disabled={filterDisableCheck("video_interpolation")}
          />
        </div>
      </div>
      <div id="video_deinterlacing">
        <div className="m-3">
          <SwitchComponent
            value={deinterlace}
            setValue={setDeinterlace}
            name="Video Deinterlacing"
            disabled={filterDisableCheck("video_deinterlacing")}
          />
        </div>
      </div>
      <div id="speech_enhancement">
        <div className="m-3">
          <SwitchComponent
            value={speech}
            setValue={setSpeech}
            name="Speech Enhancement"
            disabled={voiceDisabled || filterDisableCheck("speech_enhancement")}
          />
        </div>
      </div>
      <div id="transcription">
        <div className="m-3 flex-row">
          <SwitchComponent
            value={transcription}
            setValue={setTranscription}
            name="Transcription"
            disabled={voiceDisabled || filterDisableCheck("transcription")}
          />
          {transcription === true && (
            <p className="font-semibold pl-[52px]">Generate .srt file*</p>
          )}
        </div>
      </div>
      {showProcess === true && (
        <div>
          <div className="ml-3 mb-4">
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
