;======================================================================
;  Sun glint removal script for ENV/IDL
;  
;  Copyright (c) 2012 Luke Pinner
;  Permission is hereby granted, free of charge, to any person obtaining a 
;  copy of this software and associated documentation files (the "Software"), 
;  to deal in the Software without restriction, including without limitation 
;  the rights to use, copy, modify, merge, publish, distribute, sublicense, 
;  and/or sell copies of the Software, and to permit persons to whom the Software 
;  is furnished to do so, subject to the following conditions:
;  The above copyright notice and this permission notice shall be included 
;  in all copies or substantial portions of the Software.
;  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
;  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
;  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
;  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
;  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN 
;  CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
;
;  Reference: 
;      Hedley, JD, Harborne, AR and Mumby PJ (2005)
;      Simple and robust removal of sun glint for mapping shallow-water benthos
;      International Journal of Remote Sensing 26 (10), pp 2107–2112.
;      
;  Notes:
;      If you have any land in your image, this method will make it look terrible. 
;      As is stated in Hedley et al. (2005): "the algorithm is valid only for submerged pixels".
;      
;      Only run this tool prior to pansharpening as:
;         a. You must be able to fit the entire image in memory
;         b. It will take a lot longer otherwise...
;      
;  Installation:
;     Copy deglint.sav to the ENVI "save_add" directory:
;         ENVI 4.8 - C:\Program Files\ITT\IDL\IDL80\products\envi48\save_add
;         ENVI 5.0 (Classic) - C:\Program Files\Exelis\ENVI50\classic\save_add
;     Next time you start ENVI 4.8 or ENVI 5.0 (Classic) there will be a "Deglint" 
;     tool in the Spectral menu.
;           
;  Usage:
;     Open and display the image you want to deglint. Start the ROI tool and define 
;     an ROI containing a number of samples of areas of deep water. 
;     Select the "Spectral"->"Deglint" menu option and follow the prompts. 
;           
;  Compiled to .sav with:
;    .full_reset_session
;    resolve_all, /continue_on_error
;    .compile '<path>\deglint.pro'
;    save, file='<path>\deglint.sav', /routines
;
;======================================================================
PRO DEGLINT_DEFINE_BUTTONS, buttonInfo
    compile_opt IDL2 
    envi_define_menu_button, buttonInfo, $
       value = 'Deglint', uvalue = 'Deglint', $
       event_pro = 'DEGLINT', $ 
       ref_value = 'Spectral', position = 'last'
END

PRO DEGLINT,arg
    compile_opt IDL2

    ;near infrared wavelength min/max
    nir=[0.75,0.90]
    
    ;wavelengths
    wlname=['um','nm', 'v','GHz','MHz','Index','Unknown']
        
    ;get a file
    ENVI_SELECT, fid=fid, pos=pos, dims=dims, title='File to deglint', /no_dims, /no_spec
    if (fid[0] eq -1) then return

    ;get file info, particularly bandnames and wavelengths
    ;envi_file_query, fid, bnames=bnames,wl=wl 
    envi_file_query, fid, bbl=bbl, bnames=bnames,         $
                     class_names=class_names,             $
                     data_gains=data_gains,               $
                     data_ignore_value=data_ignore_value, $
                     data_offsets=data_offsets,           $
                     def_stretch=def_stretch,             $
                     descrip=descrip,                     $
                     file_type=file_type,                 $
                     fwhm=fwhm,                           $
                     reflectance_scale_factor=rfs,        $
                     sensor_type=sensor_type,             $
                     spec_names=spec_names,               $
                     wavelength_units=wavelength_units,   $
                     wl=wl,                               $ 
                     xstart=xstart,                       $ 
                     ystart=ystart
    
    ;Default band number for NIR band selection
    if (fwhm[0] eq -1) then begin
        nirband = where(wl ge nir[0] and wl le nir[1])
    endif else begin
        nirband = where(wl ge (nir[0]-fwhm) and wl le (nir[1]+fwhm))
    endelse

    ;Get a ROI that is a sample of deep water
    roi_ids = envi_get_roi_ids(fid=fid,roi_names=roi_names) 
    if (roi_ids[0] eq -1)then begin
        envi_report_error, 'No ROIs found! Create ROIs containing selected deep water areas and try again.'
        return
    endif
    
    ;set up widgets
    base = widget_auto_base(title='Deglint water')  
    scol = widget_base(base, /column)
    srow = widget_base(scol, /row)
    wss = widget_slabel(srow, prompt='NIR band:',XSIZE=15)
    wb = widget_pmenu(srow, list=bnames+' ['+string(wl,format='(D0.2)')+wlname[0]+']', $
                      uvalue='nirband',default=max([0,nirband[0]]), /auto)
    srow = widget_base(scol, /row)
    wss = widget_slabel(srow, prompt='Deep water ROI:',XSIZE=15,/frame)
    wr = widget_pmenu(srow, list=roi_names, uvalue='roi_id',default=0, /auto)
    wo = widget_outfm(base, uvalue='outf', /auto)

    result=auto_wid_mng(base)  
    if (result.accept eq 0) then return
    nirband=result.nirband
    roi_id=roi_ids[result.roi_id]
    in_memory=result.outf.in_memory
    filename=result.outf.name
        
    ENVI_GET_ROI_INFORMATION, roi_id,npts=npts
    if (npts eq 0) then begin
        envi_report_error, 'No ROIs found! Create ROIs containing selected deep water areas and try again.'
        return
    endif  
    
    ;Get NIR sample and data
    nirs = ENVI_GET_ROI_DATA(roi_id, FID=fid[0], pos=nirband)
    nird = ENVI_GET_DATA(FID=fid, pos=nirband,dims=dims)
    d=size(nirs,/dim)
    i=where(nirs gt 0)
    o=where(nird eq 0)
    m=min(nirs[i])
    out=0
    print, 'Minimum sampled NIR',m
    print, 'Size',d

    foreach b, pos do begin 
     
        sample = ENVI_GET_ROI_DATA(roi_id, FID=fid, pos=b)
        data = ENVI_GET_DATA(FID=fid, pos=b, dims=dims)
    
        print, 'Processing band',b+1
    
        r=linfit(nirs[i],sample[i])
        deglint=long(data - r[1] * (nird - m)+0.5) 
    
        deglint[o]=0
        neg=where(deglint lt 0)
        deglint[neg]=0
        
        if size(out, /n_dimensions) eq 0 then                 $  ;Image stack doesn't exist yet
          out=temporary(deglint)                              $
        else                                                  $  ;Concatenate image to stack
          out=[[[temporary(out)]],[[temporary(deglint)]]]
    
    endforeach
    
    map_info=envi_get_map_info(fid=fid)
    def_stretch=envi_default_stretch_create(/linear, val1=0, val2=255)

    if (in_memory eq 1) then begin
        envi_enter_data, out, bbl=bbl, bnames=bnames,         $
                         class_names=class_names,             $
                         data_gains=data_gains,               $
                         data_ignore_value=data_ignore_value, $
                         data_offsets=data_offsets,           $
                         descrip=descrip,                     $
                         file_type=file_type,                 $
                         fwhm=fwhm,                           $
                         reflectance_scale_factor=rfs,        $
                         sensor_type=sensor_type,             $
                         spec_names=spec_names,               $
                         wavelength_units=wavelength_units,   $
                         wl=wl,                               $ 
                         xstart=xstart,                       $ 
                         ystart=ystart,                       $
                         def_stretch=def_stretch,             $
                         map_info=map_info
    endif else begin
        envi_write_envi_file, out, bbl=bbl, bnames=bnames,    $
                         class_names=class_names,             $
                         data_gains=data_gains,               $
                         data_ignore_value=data_ignore_value, $
                         data_offsets=data_offsets,           $
                         descrip=descrip,                     $
                         file_type=file_type,                 $
                         fwhm=fwhm,                           $
                         reflectance_scale_factor=rfs,        $
                         sensor_type=sensor_type,             $
                         spec_names=spec_names,               $
                         wavelength_units=wavelength_units,   $
                         wl=wl,                               $ 
                         xstart=xstart,                       $ 
                         ystart=ystart,                       $
                         def_stretch=def_stretch,             $
                         map_info=map_info,                   $
                         out_name=filename
    endelse

    print, 'done'
    
END


;
;;Save the code to a file with a ".pro" extension
;;Start "ENVI + IDL" (not ENVI)
;;Load your WV2 image into ENVI.
;;In the main ENVI toolbar click File-> Export to IDL variable and export the WV2 as variable called "data"
;;Create an ROI of a variety of deep ocean areas
;;In the ROI tool dialog, select File->Subset data via ROIs
;;In the main ENVI toolbar click File-> Export to IDL variable and export the subset as variable called "samples"
;
;nirs=samples[*,*,6] ;NIR sample band, only appropriate for DG WV2 8 band
;nird=data[*,*,6]
;d=size(nirs,/dim)
;i=where(nirs gt 0)
;o=where(nird eq 0)
;m=min(nirs[i])
;out=0
;print, 'Minimum sampled NIR',m
;print, 'Size',d
;
;;foreach b, bindgen(6) do begin ;Only process bands 1-6. No point applying to NIR 1 & 2 (band 7 & 8) 
;foreach b, bindgen(8) do begin ;Process all bands even though there's no point applying to NIR 1 & 2 (band 7 & 8)
;                               ;as it makes it easier to import header info from original file 
;    print, 'Processing band',b+1
;
;    band=samples[*,*,b]
;    r=linfit(nirs[i],band[i])
;    band=data[*,*,b]
;    deglint=long(band - r[1] * (nird - m)+0.5) 
;
;    deglint[o]=0
;    if size(out, /n_dimensions) eq 0 then                 $  ;Image stack doesn't exist yet
;      out=temporary(deglint)                              $
;    else                                                  $  ;Concatenate image to stack
;      out=[[[temporary(out)]],[[temporary(deglint)]]]
;
;endforeach
;
;print, 'done'
;end
