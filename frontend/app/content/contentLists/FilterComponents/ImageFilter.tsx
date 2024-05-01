"use client";
import { useEffect, useState } from "react";
import { CustomDropdown, SwitchComponent } from "./UIComponents'";
import { Button } from "@mantine/core";
import { toast } from "sonner";
import { useMutation } from "@tanstack/react-query";
import { registerJob, getJobEstimate } from "../../../api/index";
import { useRouter } from "next/navigation";

interface ImageModel {
  id: number;
  name: string;
}

interface FiltersData {
  [key: string]: {
    active: boolean;
    model?: string;
    factor?: ImageModel;
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
export function ImageFilter(props: any) {
  const userTier = props.filterConfig["user_tier"];
  const tierConfig = props.filterConfig["model_tier"][userTier];
  const contentRes =
    props.filterConfig["content_data"]["resolution"].split("x");
  const maxFilter = tierConfig["image"]["max_filters"] as number;
  const [userMsg, setUserMsg] = useState("");
  const [estimate, setEstimate] = useState("");
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

  const [SRActive, setSRActive] = useState(false);
  const [modelType, setModelType] = useState(video_models[0]);
  const [deblur, setDeblur] = useState(false);
  const [denoise, setDenoise] = useState(false);
  const [facerestore, setFacerestore] = useState(false);
  const [colorizer, setColorizer] = useState(false);
  const [removebg, setRemoveBG] = useState(false);
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
        setEstimate(`Credit: ${data}`);
      },
      onError: () => {
        setEstimate(`Credit: 0`);
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
  }, [
    SRActive,
    deblur,
    denoise,
    facerestore,
    colorizer,
    removebg,
    maxFilter,
    modelType,
  ]);

  return (
    <div>
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
      <div id="image_deblurring">
        <div className="m-3">
          <SwitchComponent
            value={deblur}
            setValue={setDeblur}
            name="Image Deblurring"
            diasbled={filterDisableCheck("image_deblurring")}
          />
        </div>
      </div>
      <div id="image_denoising">
        <div className="m-3">
          <SwitchComponent
            value={denoise}
            setValue={setDenoise}
            name="Image Denoising"
            diasbled={filterDisableCheck("image_denoising")}
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
      <div id="remove_background">
        <div className="ml-3 mr-3 mt-3 mb-2 flex-row">
          <SwitchComponent
            value={removebg}
            setValue={setRemoveBG}
            name="Remove Background"
            disabled={filterDisableCheck("remove_background")}
          />
        </div>
      </div>
      {showProcess === true && (
        <div className="ml-3">
          <p>{estimate}</p>
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
