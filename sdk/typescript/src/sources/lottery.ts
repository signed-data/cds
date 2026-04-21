// Updated LotteryContentTypes
const LotteryContentTypes = {
    MEGA_SENA: { uri: 'desired_uri_for_mega_sena', mime_type: 'application/vnd.cds.lottery-brazil.mega-sena-result+json;v=1' },
    LOTTO: { uri: 'desired_uri_for_lotto', mime_type: 'application/vnd.cds.lottery-brazil.lotto-result+json;v=1' },
    POWERBALL: { uri: 'desired_uri_for_powerball', mime_type: 'application/vnd.cds.lottery-brazil.powerball-result+json;v=1' }
    // Add other lottery types as needed
};

// Update MegaSenaIngestor
MegaSenaIngestor.contentType = LotteryContentTypes.MEGA_SENA.uri;

// Update CDSEvent content_type
CDSEvent.content_type = LotteryContentTypes.MEGA_SENA.uri;