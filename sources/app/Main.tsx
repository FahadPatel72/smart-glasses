import * as React from 'react';
import { SafeAreaView, StyleSheet, View, Button } from 'react-native';
import { RoundButton } from './components/RoundButton';
import { Theme } from './components/theme';
import { useDevice } from '../modules/useDevice';
import { DeviceView } from './DeviceView';
import { textToSpeech } from '../modules/openai'; // Import the textToSpeech function

const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();

export const Main = React.memo(() => {
    const [device, connectDevice] = useDevice();
    
    const handlePlayAudio = async () => {
        // Resume AudioContext if needed
        if (audioContext.state === 'suspended') {
            await audioContext.resume();
        }

        // Call textToSpeech function
        // await textToSpeech();
    };

    return (
        <SafeAreaView style={styles.container}>
            {!device && (
                <View style={styles.buttonContainer}>
                    <RoundButton title="Connect to the device" action={connectDevice} />
                </View>
            )}
            {device && (
                <>
                    <DeviceView device={device} />
                    <View style={styles.audioButtonContainer}>
                        <Button title="Play Audio" onPress={handlePlayAudio} />
                    </View>
                </>
            )}
        </SafeAreaView>
    );
});

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: Theme.background,
        alignItems: 'stretch',
        justifyContent: 'center',
    },
    buttonContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        alignSelf: 'center',
    },
    audioButtonContainer: {
        marginTop: 20, // Adjust as needed
        alignItems: 'center',
    }
});
