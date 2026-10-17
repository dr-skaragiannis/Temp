plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "org.meshcrowd.meter"
    compileSdk = 35

    defaultConfig {
        applicationId = "org.meshcrowd.meter"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "meter-1.0"
    }

    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
            // Use your own keystore for a release build that behaves like the campaign APK.
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }

    sourceSets {
        getByName("main") {
            // reuse the probe classes so Route A and Route B measure with identical code
            java.srcDirs("src/main/java", "../../probes")
        }
    }
}

dependencies { }
