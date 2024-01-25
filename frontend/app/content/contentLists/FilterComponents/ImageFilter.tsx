"use client";
import { useState } from "react";
import { CustomDropdown, SwitchComponent } from "./UIComponents'";
import { Button } from "@mantine/core";
import { toast } from "sonner";
import { useMutation } from "@tanstack/react-query";
import { registerJob } from "../../../api/index";
import { useRouter } from "next/navigation";

export function ImageFilter(props: any) {
  const { push } = useRouter();
  const video_models = [
    { id: 1, name: "SuperRes 2x v1 (Faster)" },
    { id: 2, name: "SuperRes 4x v1 (Faster)" },
    { id: 3, name: "SuperRes 2x v2 (Slower, better result)" },
    { id: 4, name: "SuperRes 4x v2 (Slower, better result)" },
    { id: 5, name: "SuperRes Anime (For Animated content)" },
  ];

  const [SRActive, setSRActive] = useState(false);
  const [modelType, setModelType] = useState(video_models[0]);
  const [deblur, setDeblur] = useState(false);
  const [denoise, setDenoise] = useState(false);
  const [facerestore, setFacerestore] = useState(false);
  const [colorizer, setColorizer] = useState(false);
  const [removebg, setRemoveBG] = useState(false);

  function sleep(ms: number) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  const createJSON = () => {
    const filters_data = {
      super_resolution: {
        active: SRActive,
        model: modelType.name,
      },
      image_deblurring: {
        active: deblur,
      },
      image_denoising: {
        active: denoise,
      },
      face_restoration: {
        active: facerestore,
      },
      bw_to_color: {
        active: colorizer,
      },
      remove_background: {
        active: removebg,
      },
    };
    const data = {
      content_id: props.id,
      content_type: "image",
      filters: filters_data,
    };
    return data;
  };

  const { mutate, isLoading, isSuccess } = useMutation(
    (formData) => registerJob("image", formData),
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
      job_type: "image",
      job_data: data,
    };
    mutate(jobData as any);
    props.setFilterShow(false);
    await sleep(2000);
    push("/jobs");
  };

  return (
    <div>
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
      <div id="image_deblurring">
        <div className="m-3">
          <SwitchComponent
            value={deblur}
            setValue={setDeblur}
            name="Image Deblurring"
          />
        </div>
      </div>
      <div id="image_denoising">
        <div className="m-3">
          <SwitchComponent
            value={denoise}
            setValue={setDenoise}
            name="Image Denoising"
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
      <div id="remove_background">
        <div className="m-3">
          <SwitchComponent
            value={removebg}
            setValue={setRemoveBG}
            name="Remove Background"
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
