// Update Detailed Timing
$(function($){
	function toggle_flags() {
		var flags_sync_scheme = $("select[name=flags_sync_scheme]").val();

//		analog_composite = flags_sync_scheme == 0 ? true : false;
//		bipolar_analog_composite = flags_sync_scheme == 1 ? true : false;
		digital_composite = flags_sync_scheme == 2 ? true : false;
		digital_separate = flags_sync_scheme == 3 ? true : false;

		//If flags_sync_scheme == Digital_Separate
		$('#div_id_flags_horizontal_polarity').toggle(digital_separate);
		$('#div_id_flags_vertical_polarity').toggle(digital_separate);

    	//If not flags_sync_scheme == Digital_Separate
		$('#div_id_flags_serrate').toggle(!digital_separate);

	    //If flags_sync_scheme == Digital_Composite
		$('#div_id_flags_composite_polarity').toggle(digital_composite);

	    //If not flags_sync_scheme == Digital_Composite and not flags_sync_scheme == Digital_Separate
		$('#div_id_flags_sync_on_RGB').toggle(!digital_composite && !digital_separate);
	}

	$("#id_flags_sync_scheme").click(toggle_flags);
	$(document).ready(toggle_flags);
});
