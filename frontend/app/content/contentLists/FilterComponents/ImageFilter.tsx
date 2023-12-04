"use client";
import { useState } from "react";
import { CustomDropdown, SwitchComponent } from "./UIComponents'";
import { Button } from "@mantine/core";
import { toast } from "sonner";
import { useMutation } from "@tanstack/react-query";
import { registerJob } from "../../../api/index";

export function ImageFilter(props: any) {
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

  const createJSON = () => {
    const filters_data = {
      super_resolution: {
        active: SRActive,
        model: modelType.name,
      },
      deblur: {
        active: deblur,
      },
      denoise: {
        active: denoise,
      },
      face_restoration: {
        active: facerestore,
      },
      colorizer: {
        active: colorizer,
      },
      remove_bg: {
        active: removebg,
      },
    };
    const data = {
      content_id: props.id,
      content_type: "image",
      filters: filters_data,
    };
    return data;
  }

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

  const sendJob = () => {
    const data = createJSON();
    const jobData = {
      job_type: "image",
      job_data: data,
    }
    mutate(jobData as any);
    props.setFilterShow(false);
  }

  return (
    <div>
      <div id="sr" className="">
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
      <div id="deblur">
        <div className="m-3">
          <SwitchComponent
            value={deblur}
            setValue={setDeblur}
            name="Image Deblurring"
          />
        </div>
      </div>
      <div id="denoise">
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
      <div id="b/w">
        <div className="m-3">
          <SwitchComponent
            value={colorizer}
            setValue={setColorizer}
            name="B/W to Color"
          />
        </div>
      </div>
      <div id="remove-bg">
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
          <Button variant="outline" color="grape" radius="md" onClick={sendJob}>
            Process
          </Button>
        </div>
      </div>
    </div>
  );
}
