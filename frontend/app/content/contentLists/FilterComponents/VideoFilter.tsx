"use client";
import { useState, useEffect } from "react";
import { CustomDropdown, SwitchComponent } from "./UIComponents'";
import { Button } from "@mantine/core";
import { toast } from "sonner";
import { useMutation } from "@tanstack/react-query";
import { registerJob } from "../../../api/index";
import { useRouter } from "next/navigation";

export function VideoFilter(props: any) {
  const { push } = useRouter();
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
  const [modelType, setModelType] = useState(video_models[0]);
  const [deblur, setDeblur] = useState(false);
  const [denoise, setDenoise] = useState(false);
  const [facerestore, setFacerestore] = useState(false);
  const [colorizer, setColorizer] = useState(false);
  const [slowmo, setSlowmo] = useState(false);
  const [slowmofactor, setSlowmoFactor] = useState(slowmo_factor[0]);
  const [interpolation, setInterpolation] = useState(false);
  const [deinterlace, setDeinterlace] = useState(false);
  const [speech, setSpeech] = useState(false);
  const [transcription, setTranscription] = useState(false);
  const [voiceDisabled, setVoiceDisabled] = useState(false);
  const [slowmodisabled, setSlowmodisabled] = useState(false);
  const [showProcess, setShowProcess] = useState(false);

  function sleep(ms: number) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  const createJSON = () => {
    const filters_data = {
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
    const data = {
      content_id: props.id,
      content_type: "video",
      filters: filters_data,
    };
    return data;
  };

  const { mutate, isLoading, isSuccess } = useMutation(
    (formData) => registerJob("video", formData),
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
      job_type: "video",
      job_data: data,
    };
    mutate(jobData as any);
    props.setFilterShow(false);
    await sleep(2000);
    push("/jobs");
  };

  useEffect(() => {
    if (slowmo === true) {
      setVoiceDisabled(true);
    } else {
      setVoiceDisabled(false);
    }
    if (speech === true || transcription === true) {
      setSlowmodisabled(true);
    }
    if (speech === false && transcription === false) {
      setSlowmodisabled(false);
    }
    if (
      SRActive === true ||
      deblur === true ||
      denoise === true ||
      facerestore === true ||
      colorizer === true ||
      slowmo === true ||
      interpolation === true ||
      deinterlace === true ||
      speech === true ||
      transcription === true
    ) {
      setShowProcess(true);
    } else {
      setShowProcess(false);
    }
  }, [
    slowmo,
    voiceDisabled,
    transcription,
    speech,
    showProcess,
    setShowProcess,
    SRActive,
    deblur,
    denoise,
    facerestore,
    colorizer,
    interpolation,
    deinterlace,
  ]);

  return (
    <div className="overflow-y-auto">
      <div id="super_resolution" className="">
        <div className="m-3">
          <SwitchComponent
            value={SRActive}
            setValue={setSRActive}
            name="Super Resolution"
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
          />
        </div>
      </div>
      <div id="video_denoising">
        <div className="m-3">
          <SwitchComponent
            value={denoise}
            setValue={setDenoise}
            name="Video Denoising"
          />
        </div>
      </div>
      <div id="face_restoration">
        <div className="m-3">
          <SwitchComponent
            value={facerestore}
            setValue={setFacerestore}
            name="Face Restoration"
          />
        </div>
      </div>
      <div id="bw_to_color">
        <div className="m-3">
          <SwitchComponent
            value={colorizer}
            setValue={setColorizer}
            name="B/W to Color"
          />
        </div>
      </div>
      <div id="slow_motion" className="">
        <div className="m-3">
          <SwitchComponent
            value={slowmo}
            setValue={setSlowmo}
            name="Slow Motion"
            disabled={slowmodisabled}
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
          />
        </div>
      </div>
      <div id="video_deinterlacing">
        <div className="m-3">
          <SwitchComponent
            value={deinterlace}
            setValue={setDeinterlace}
            name="Video Deinterlacing"
          />
        </div>
      </div>
      <div id="speech_enhancement">
        <div className="m-3">
          <SwitchComponent
            value={speech}
            setValue={setSpeech}
            name="Speech Enhancement"
            disabled={voiceDisabled}
          />
        </div>
      </div>
      <div id="transcription">
        <div className="m-3 flex-row">
          <SwitchComponent
            value={transcription}
            setValue={setTranscription}
            name="Transcription"
            disabled={voiceDisabled}
          />
          {transcription === true && (
            <p className="font-semibold pl-[52px]">Generate .srt file*</p>
          )}
        </div>
      </div>
      {showProcess === true && (
        <div>
          <div className="ml-3 mb-4">
            <p>Total Price : 3.4 credits </p>
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
    </div>
  );
}
