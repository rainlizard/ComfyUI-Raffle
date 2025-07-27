import torch

class CurvedRescaleCFG:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "model": ("MODEL",),
                              "multiplier": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 1000000.0, "step": 0.01}),
                              "curve_peak_position": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
                              "curve_sharpness": ("FLOAT", {"default": 2.0, "min": 0.01, "max": 1000000.0, "step": 0.01}),
                              }}
    RETURN_TYPES = ("MODEL",)
    FUNCTION = "patch"

    CATEGORY = "advanced/model"

    def patch(self, model, multiplier, curve_peak_position, curve_sharpness):
        def rescale_cfg_advanced_wrapper(args):
            nonlocal multiplier, curve_peak_position, curve_sharpness

            cond = args["cond"]
            uncond = args["uncond"]
            cond_scale = args["cond_scale"]
            current_sigma_tensor = args["sigma"]
            x_orig = args["input"]

            if cond is None or uncond is None or cond_scale is None or current_sigma_tensor is None or current_sigma_tensor.numel() == 0 or x_orig is None:
                return args.get("uncond_denoised", args.get("cond_denoised", x_orig))

            current_sigma = current_sigma_tensor[0].item()

            # Calculate normalized progress (0 at high sigma, 1 at low sigma)
            # Using log scale for better distribution across sigma range
            sigma_normalized = max(0.0, min(1.0, 1.0 - (torch.log(current_sigma_tensor[0] + 1e-10) + 5) / 8))

            # Apply bell curve that starts at 0, peaks at curve_peak_position, and returns to 0
            # Calculate distance from peak position
            distance_from_peak = abs(sigma_normalized - curve_peak_position)

            # Calculate maximum possible distance (furthest edge from peak)
            max_distance = max(curve_peak_position, 1.0 - curve_peak_position)

            # Normalize distance: 0 at peak, 1 at furthest edge
            normalized_distance = distance_from_peak / max_distance if max_distance > 0 else 0

            # Create bell curve: 1 at peak, 0 at edges
            # Higher curve_sharpness makes the peak sharper/narrower
            curve_value = (1.0 - normalized_distance) ** curve_sharpness

            dynamic_multiplier = multiplier * curve_value

            sigma_view = current_sigma_tensor.view(current_sigma_tensor.shape[:1] + (1,) * (cond.ndim - 1))
            x = x_orig / (sigma_view * sigma_view + 1.0)
            v_pred_cond = ((x - x_orig + cond) * (sigma_view ** 2 + 1.0) ** 0.5) / sigma_view
            v_pred_uncond = ((x - x_orig + uncond) * (sigma_view ** 2 + 1.0) ** 0.5) / sigma_view
            v_pred_cfg = v_pred_uncond + cond_scale * (v_pred_cond - v_pred_uncond)
            ro_pos = torch.std(v_pred_cond, dim=tuple(range(1, v_pred_cond.ndim)), keepdim=True)
            ro_cfg = torch.std(v_pred_cfg, dim=tuple(range(1, v_pred_cfg.ndim)), keepdim=True)
            factor = torch.nan_to_num(ro_pos / (ro_cfg + 1e-5), nan=1.0, posinf=1.0, neginf=1.0)
            v_pred_final = dynamic_multiplier * (v_pred_cfg * factor) + (1.0 - dynamic_multiplier) * v_pred_cfg
            return x_orig - (x - v_pred_final * sigma_view / (sigma_view * sigma_view + 1.0) ** 0.5)

        m = model.clone()
        m.set_model_sampler_cfg_function(rescale_cfg_advanced_wrapper)
        return (m, )

NODE_CLASS_MAPPINGS = {
    "CurvedRescaleCFG": CurvedRescaleCFG,
}
