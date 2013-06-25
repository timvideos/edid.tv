$(function($){
	// Basic Display Parameters, video input
	function toggle_bdp() {
		var bdp_video_input = $("input:radio[name=bdp_video_input]:checked").val();
		//Analog: false, Digital: true
		bdp_video_input = bdp_video_input == 0 ? false : true;

		//Analog
		$('#div_id_bdp_signal_level_standard').toggle(!bdp_video_input);
		$('#div_id_bdp_blank_to_black_setup').toggle(!bdp_video_input);
		$('#div_id_bdp_separate_syncs').toggle(!bdp_video_input);
		$('#div_id_bdp_composite_sync').toggle(!bdp_video_input);
		$('#div_id_bdp_sync_on_green_video').toggle(!bdp_video_input);
		$('#div_id_bdp_vsync_serration').toggle(!bdp_video_input);

		//Digital
		$('#div_id_bdp_video_input_DFP_1').toggle(bdp_video_input);
	}

	$("input:radio[name=bdp_video_input]").click(toggle_bdp);
	$(document).ready(toggle_bdp);


	// Monitor Range Limits
	function toggle_mrl() {
		// Main fields are bound to mrl value
		var mrl = !$('#id_monitor_range_limits').is(":checked");
		$('#id_mrl_min_horizontal_rate').prop('disabled', mrl);
		$('#id_mrl_max_horizontal_rate').prop('disabled', mrl);
		$('#id_mrl_min_vertical_rate').prop('disabled', mrl);
		$('#id_mrl_max_vertical_rate').prop('disabled', mrl);
		$('#id_mrl_max_pixel_clock').prop('disabled', mrl);
		$('#id_mrl_secondary_GTF_curve_supported').prop('disabled', mrl);

		if (mrl) {
			// If mrl value is disabled, bound Secondary GTF fields to it
			$('#id_mrl_secondary_GTF_start_frequency').prop('disabled', mrl);
			$('#id_mrl_secondary_GTF_C').prop('disabled', mrl);
			$('#id_mrl_secondary_GTF_M').prop('disabled', mrl);
			$('#id_mrl_secondary_GTF_K').prop('disabled', mrl);
			$('#id_mrl_secondary_GTF_J').prop('disabled', mrl);
		} else {
			// If mrl value is enabled, bound Secondary GTF fields to Secondary GTF value
			var mrl_secondary_GTF = !$('#id_mrl_secondary_GTF_curve_supported').is(":checked");
			$('#id_mrl_secondary_GTF_start_frequency').prop('disabled', mrl_secondary_GTF);
			$('#id_mrl_secondary_GTF_C').prop('disabled', mrl_secondary_GTF);
			$('#id_mrl_secondary_GTF_M').prop('disabled', mrl_secondary_GTF);
			$('#id_mrl_secondary_GTF_K').prop('disabled', mrl_secondary_GTF);
			$('#id_mrl_secondary_GTF_J').prop('disabled', mrl_secondary_GTF);
		}
	}

	$('#id_monitor_range_limits').click(toggle_mrl);
	$('#id_mrl_secondary_GTF_curve_supported').click(toggle_mrl);

	$(document).ready(toggle_mrl);
});
