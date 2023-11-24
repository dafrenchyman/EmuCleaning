#!/bin/bash
zipSourceLocation="/ROMs/7zipped_ps2/"
csoDestinationLocation="/ROMS/ps2/"

cd "${zipSourceLocation}"
for zipFile in *.7z; do
	gameName="$(basename "$zipFile" .7z)"

	echo "------------------------------------"
	echo "Converting ${gameName}..."
	echo "------------------------------------"

	# Get list of filenames in the zip file
	gameFileName=`7z -slt l "${zipFile}" | grep -oP "(?<=Path = ).+" | tail -n +2`
	nameInZip="$(basename "$gameFileName")"
	extensionInZip="${gameFileName##*.}"
	zipBaseName="${nameInZip%.*}"
	finalCsoFilename="${csoDestinationLocation}${gameName} [${zipBaseName}].cso"

	echo "Source file: ${zipSourceLocation}${zipFile}"
	echo "Original filename: ${gameFileName}"
	echo "Extension: ${extensionInZip}"
	echo "Destination: ${finalCsoFilename}"

	# If we've already processed the cso file skip it
	if [[ -f "$finalCsoFilename" ]]; then
		echo "Skipping game already prepared: ${finalCsoFilename}"
		continue
	fi

	mkdir -p "${csoDestinationLocation}${gameName}"
	echo "unzipping..."
	7z x -o"${csoDestinationLocation}${gameName}" "${zipFile}"
	echo "converting..."

	cd "${csoDestinationLocation}${gameName}"
	for binFile in *.bin; do
		[ -f "$binFile" ] || break
		echo "${binFile}"
		binName="$(basename "$binFile" .bin)"
		cueFilename="${binName}.cue"
		echo -e "FILE\"${gameFileName}\" BINARY\nTRACK 01 MODE2/2352\nINDEX 01 00:00:00" > "${csoDestinationLocation}${gameName}/${cueFilename}"
		bchunk "${binName}.bin" "${binName}.cue" "${binName}"

		# bchunk adds a 01 (for the track number to the filename). Need to remove that
		bchunkName="${binName}01.iso"
		mv "${bchunkName}" "${binName}.iso"

	done

	for isoFile in *.iso; do
		isoName="$(basename "$isoFile" .iso)"
		newIsoFileName="${gameName} [${isoName}].iso"
		mv "${isoFile}" "${newIsoFileName}"

		newCsoFileName="$(basename "$newIsoFileName" .iso).cso"
		ciso 9 "${newIsoFileName}" "${newCsoFileName}"
		mv "${newCsoFileName}" "../${newCsoFileName}"

		# Delete the iso file
		rm "${newIsoFileName}"
	done
	#chdman createcd --force -i "${gameName}/${cueFile}" -o "../chd/${gameName}.chd"
	echo "cleanup..."
	cd ..
	rm -rf "${csoDestinationLocation}${gameName}"
	cd "${zipSourceLocation}"
done

echo "All done."